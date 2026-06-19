#!/bin/sh
# ============================================================
# MinIO 初始化脚本（精简版）
# 使用 mc ilm rule add 命令行方式（比 JSON import 更可靠）
# ============================================================

set -e

echo '等待 MinIO 就绪...'
sleep 10

until mc alias set hot http://minio-hot:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null; do
  echo '等待热节点...' && sleep 3
done

until mc alias set cold http://minio-cold:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null; do
  echo '等待冷节点...' && sleep 3
done

echo ''
echo '=== 1. 创建存储桶 ==='
mc mb hot/radar-data  --region=cn-east-1 2>/dev/null && echo '  ✅ radar-data 创建成功' || echo '  ℹ️  已存在'
mc mb hot/radar-archive --region=cn-east-1 2>/dev/null && echo '  ✅ radar-archive 创建成功' || echo '  ℹ️  已存在'
mc mb cold/radar-archive-cold --region=cn-east-1 2>/dev/null && echo '  ✅ radar-archive-cold 创建成功' || echo '  ℹ️  已存在'

mc tag set hot/radar-data 'retention=hot&type=realtime'
mc tag set hot/radar-archive 'retention=warm&type=archive'

echo ''
echo '=== 2. 配置分层存储 ==='
mc admin tier add minio hot COLD-TIER \
  --endpoint http://minio-cold:9000 \
  --access-key radaradmin \
  --secret-key 'RadarAdmin@2024!' \
  --bucket radar-archive-cold \
  --region cn-east-1 2>/dev/null && echo '  ✅ COLD-TIER 分层创建成功' || echo '  ℹ️  分层已存在'

echo ''
echo '=== 3. 设置 ILM 生命周期策略 ==='

# radar-data: 7天→冷, 90天过期
mc ilm rule add hot/radar-data \
  --transition-days 7 --transition-tier COLD-TIER \
  --expire-days 90 \
  --noncurrent-expire-days 180 \
  --noncurrent-transition-days 7 --noncurrent-transition-tier COLD-TIER 2>/dev/null \
  && echo '  ✅ radar-data: 7天→冷, 90天过期' \
  || echo '  ℹ️  radar-data ILM 已存在'

# radar-archive: 30天→冷, 365天过期
mc ilm rule add hot/radar-archive \
  --transition-days 30 --transition-tier COLD-TIER \
  --expire-days 365 \
  --noncurrent-expire-days 365 \
  --noncurrent-transition-days 30 --noncurrent-transition-tier COLD-TIER 2>/dev/null \
  && echo '  ✅ radar-archive: 30天→冷, 365天过期' \
  || echo '  ℹ️  radar-archive ILM 已存在'

echo ''
echo '=== 4. 创建服务账号 ==='
mc admin user svcacct add hot radaradmin \
  --access-key radar-simulator \
  --secret-key 'RadarSim@2024!' \
  --policy /ilm/policy.json 2>/dev/null \
  && echo '  ✅ 服务账号创建成功' \
  || echo '  ℹ️  账号已存在'

echo ''
echo '=== ✅ 初始化完成 ==='
echo "  热数据: http://minio-hot:9000 (NVMe)"
echo "  冷数据: http://minio-cold:9000 (HDD)"
echo "  Nginx:  http://nginx-lb:18080"

tail -f /dev/null

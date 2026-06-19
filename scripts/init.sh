#!/bin/sh
# ============================================================
# MinIO 初始化脚本（精简版）
# 1. 创建热/冷存储桶
# 2. 配置分层存储（热→冷）
# 3. 设置 ILM 生命周期策略
# 4. 创建服务账号
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
mc mb hot/radar-data  --region=cn-east-1 || echo '  已存在'
mc mb hot/radar-archive --region=cn-east-1 || echo '  已存在'
mc mb cold/radar-archive-cold --region=cn-east-1 || echo '  已存在'

mc tag set hot/radar-data 'retention=hot&type=realtime'
mc tag set hot/radar-archive 'retention=warm&type=archive'

echo ''
echo '=== 2. 配置分层存储 ==='
mc admin tier add minio hot COLD-TIER \
  --endpoint http://minio-cold:9000 \
  --access-key radaradmin \
  --secret-key 'RadarAdmin@2024!' \
  --bucket radar-archive-cold \
  --region cn-east-1 || echo '  分层已存在'

echo ''
echo '=== 3. 设置 ILM 生命周期策略 ==='

# 热数据桶: 7天→冷存储, 90天过期
mc ilm import hot/radar-data < /ilm/ilm-hot.json || echo '  ILM已存在'

# 归档桶: 30天→冷存储, 365天过期
mc ilm import hot/radar-archive < /ilm/ilm-warm.json || echo '  ILM已存在'

echo ''
echo '=== 4. 创建服务账号 ==='
mc admin user svcacct add hot radaradmin \
  --access-key radar-simulator \
  --secret-key 'RadarSim@2024!' \
  --policy /ilm/policy.json || echo '  账号已存在'

echo ''
echo '=== ✅ 初始化完成 ==='
echo "  热数据: http://minio-hot:9000  (NVMe)"
echo "  冷数据: http://minio-cold:9000  (HDD)"
echo "  Nginx:  http://nginx-lb:18080"

tail -f /dev/null

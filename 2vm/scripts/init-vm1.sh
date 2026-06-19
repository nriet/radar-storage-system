#!/bin/sh
# ============================================================
# MinIO 初始化脚本（在 VM-1 上执行）
# 使用 mc ilm rule add 命令行方式（比 JSON import 更可靠）
# ============================================================

COLD_NODE_IP="${COLD_NODE_IP:-minio-cold}"

echo '=== MinIO 存储系统初始化 ==='

echo '[1/4] 连接节点...'
until mc alias set hot http://minio-hot:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null; do
  echo '  等待热节点...' && sleep 3
done
echo '  ✅ 热节点连接成功'

until mc alias set cold http://${COLD_NODE_IP}:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null; do
  echo '  等待冷节点...' && sleep 3
done
echo '  ✅ 冷节点连接成功'

echo ''
echo '[2/4] 创建存储桶...'
mc mb hot/radar-data --region=cn-east-1 2>/dev/null && echo '  ✅ radar-data' || echo '  ℹ️  已存在'
mc mb hot/radar-archive --region=cn-east-1 2>/dev/null && echo '  ✅ radar-archive' || echo '  ℹ️  已存在'
mc mb cold/radar-archive-cold --region=cn-east-1 2>/dev/null && echo '  ✅ radar-archive-cold' || echo '  ℹ️  已存在'

echo ''
echo '[3/4] 配置分层存储 + ILM...'
mc admin tier add minio hot COLD-TIER \
  --endpoint http://${COLD_NODE_IP}:9000 \
  --access-key radaradmin --secret-key 'RadarAdmin@2024!' \
  --bucket radar-archive-cold --region cn-east-1 2>/dev/null \
  && echo '  ✅ COLD-TIER 分层' || echo '  ℹ️  分层已存在'

# radar-data: 7天→冷, 90天过期
mc ilm rule add hot/radar-data \
  --transition-days 7 --transition-tier COLD-TIER \
  --expire-days 90 \
  --noncurrent-expire-days 180 \
  --noncurrent-transition-days 7 --noncurrent-transition-tier COLD-TIER 2>/dev/null \
  && echo '  ✅ radar-data: 7天→冷, 90天过期' || echo '  ℹ️  ILM已存在'

# radar-archive: 30天→冷, 365天过期
mc ilm rule add hot/radar-archive \
  --transition-days 30 --transition-tier COLD-TIER \
  --expire-days 365 \
  --noncurrent-expire-days 365 \
  --noncurrent-transition-days 30 --noncurrent-transition-tier COLD-TIER 2>/dev/null \
  && echo '  ✅ radar-archive: 30天→冷, 365天过期' || echo '  ℹ️  ILM已存在'

echo ''
echo '[4/4] 创建服务账号...'
mc admin user svcacct add hot radaradmin \
  --access-key radar-simulator --secret-key 'RadarSim@2024!' \
  --policy /ilm/policy.json 2>/dev/null \
  && echo '  ✅ 服务账号创建成功' || echo '  ℹ️  已存在'

echo ''
echo '=== ✅ 初始化完成 ==='
echo '  热数据:  http://VM-1-IP:9010 (radar-data)'
echo '  冷数据:  http://VM-2-IP:9020 (radar-archive-cold)'
echo '  Nginx:   http://VM-1-IP:18080'
echo '  监控:    http://VM-1-IP:8888'

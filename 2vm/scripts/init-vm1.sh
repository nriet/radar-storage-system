#!/bin/sh
# ============================================================
# MinIO 初始化脚本（在 VM-1 上执行）
# 1. 创建热数据桶
# 2. 连接冷数据节点，配置分层存储
# 3. 设置 ILM 生命周期策略
# 4. 创建模拟器服务账号
# ============================================================

COLD_NODE_IP="${COLD_NODE_IP:-minio-cold}"  # VM-2 的 IP 或主机名

echo '========================================'
echo '  MinIO 存储系统初始化'
echo '========================================'
echo ''

# 等待本机 MinIO 就绪
echo '[1/6] 连接热节点...'
until mc alias set hot http://minio-hot:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null; do
  echo '  等待热节点就绪...' && sleep 3
done
echo '  ✅ 热节点连接成功'
echo ''

# 连接冷节点
echo '[2/6] 连接冷节点...'
until mc alias set cold http://${COLD_NODE_IP}:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null; do
  echo '  等待冷节点就绪...' && sleep 3
done
echo '  ✅ 冷节点连接成功'
echo ''

# 创建存储桶
echo '[3/6] 创建存储桶...'
mc mb hot/radar-data --region=cn-east-1 2>/dev/null && echo '  ✅ hot/radar-data 创建成功' || echo '  ℹ️  hot/radar-data 已存在'
mc mb hot/radar-archive --region=cn-east-1 2>/dev/null && echo '  ✅ hot/radar-archive 创建成功' || echo '  ℹ️  hot/radar-archive 已存在'
mc mb cold/radar-archive-cold --region=cn-east-1 2>/dev/null && echo '  ✅ cold/radar-archive-cold 创建成功' || echo '  ℹ️  cold/radar-archive-cold 已存在'
echo ''

# 配置分层存储
echo '[4/6] 配置分层存储...'
mc admin tier add minio hot COLD-TIER \
  --endpoint http://${COLD_NODE_IP}:9000 \
  --access-key radaradmin \
  --secret-key 'RadarAdmin@2024!' \
  --bucket radar-archive-cold \
  --region cn-east-1 2>/dev/null && echo '  ✅ 分层存储 COLD-TIER 配置成功' || echo '  ℹ️  分层存储已存在'
echo ''

# 设置 ILM 策略
echo '[5/6] 设置 ILM 生命周期策略...'

# 热数据: 7天→冷存储, 90天过期
mc ilm import hot/radar-data < /ilm/ilm-hot.json 2>/dev/null && echo '  ✅ radar-data ILM: 7天→冷, 90天过期' || echo '  ℹ️  radar-data ILM 已存在'

# 归档: 30天→冷存储, 365天过期
mc ilm import hot/radar-archive < /ilm/ilm-warm.json 2>/dev/null && echo '  ✅ radar-archive ILM: 30天→冷, 365天过期' || echo '  ℹ️  radar-archive ILM 已存在'
echo ''

# 创建服务账号
echo '[6/6] 创建服务账号...'
mc admin user svcacct add hot radaradmin \
  --access-key radar-simulator \
  --secret-key 'RadarSim@2024!' \
  --policy /ilm/policy.json 2>/dev/null && echo '  ✅ 服务账号创建成功' || echo '  ℹ️  服务账号已存在'

echo ''
echo '========================================'
echo '  ✅ 初始化完成！'
echo '========================================'
echo ''
echo '  热数据: http://VM-1-IP:9010'
echo '  冷数据: http://VM-2-IP:9020'
echo '  Nginx:  http://VM-1-IP:18080'
echo '  监控:   http://VM-1-IP:8888'
echo ''
echo '  雷达模拟器和服务账号已就绪'
echo ''

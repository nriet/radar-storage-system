#!/bin/sh
# ============================================================
# MinIO 集群初始化脚本
# 创建存储桶、配置分层存储、设置生命周期管理
# ============================================================

set -e

echo '等待MinIO集群就绪...'
sleep 10

until (mc alias set hot http://minio-node1:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null); do
  echo '等待MinIO hot集群...' && sleep 3
done

until (mc alias set cold http://minio-cold:9000 radaradmin 'RadarAdmin@2024!' 2>/dev/null); do
  echo '等待MinIO cold集群...' && sleep 3
done

echo '=== 创建存储桶 ==='

# 创建雷达数据桶
mc mb hot/radar-data --region=cn-east-1 --with-lock || echo "radar-data 已存在"
mc mb hot/radar-archive --region=cn-east-1 --with-lock || echo "radar-archive 已存在"
mc mb hot/radar-backup --region=cn-east-1 || echo "radar-backup 已存在"

# 在冷存储上也创建桶
mc mb cold/radar-archive-cold --region=cn-east-1 || echo "radar-archive-cold 已存在"

# 设置桶标签
mc tag set hot/radar-data 'radar-type=real-time&retention=hot' || echo "标记radar-data完成"
mc tag set hot/radar-archive 'radar-type=archive&retention=warm' || echo "标记radar-archive完成"
mc tag set hot/radar-backup 'radar-type=backup&retention=warm' || echo "标记radar-backup完成"

echo '=== 配置分层存储 ==='

# 添加冷存储层 - 格式: mc admin tier add <type> <alias> <tier-name> [flags]
mc admin tier add minio hot cold-tier-s3 --endpoint http://minio-cold:9000 --access-key radaradmin --secret-key 'RadarAdmin@2024!' --bucket radar-archive-cold --region cn-east-1 || echo "分层存储已存在"

echo '=== 配置生命周期管理 ==='

# 导入ILM策略
mc ilm import hot/radar-data < /ilm/ilm-rule-hot-to-warm.json || echo "radar-data ILM导入完成"
mc ilm import hot/radar-archive < /ilm/ilm-rule-warm-to-cold.json || echo "radar-archive ILM导入完成"
mc ilm import hot/radar-backup < /ilm/ilm-rule-backup.json || echo "radar-backup ILM导入完成"

echo '=== 创建服务账号 ==='

# 创建服务账号
mc admin user svcacct add hot radaradmin --access-key radar-simulator --secret-key 'RadarSim@2024!' --policy /ilm/radar-policy.json || echo "服务账号已存在"

echo '=== 设置存储配额 ==='

mc quota set hot/radar-data --size 100GB || echo "radar-data配额设置完成"
mc quota set hot/radar-archive --size 200GB || echo "radar-archive配额设置完成"

echo '=== 初始化完成 ==='
echo 'MinIO Console: http://localhost:19111 ~ 19114'
echo '负载均衡入口: http://localhost:18080 (主) / http://localhost:28080 (备)'
echo 'VIP 入口: http://172.20.0.100:18080 (虚拟IP)'

# 持续运行
tail -f /dev/null

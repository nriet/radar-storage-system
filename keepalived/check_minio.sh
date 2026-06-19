#!/bin/sh
# ============================================================
# MinIO集群健康检查脚本
# 用于Keepalived检测MinIO集群是否可用
# ============================================================

# MinIO节点列表
MINIO_NODES="minio-node1:9000 minio-node2:9000 minio-node3:9000 minio-node4:9000"

# 可用节点计数
healthy_nodes=0
total_nodes=0

for node in $MINIO_NODES; do
    total_nodes=$((total_nodes + 1))
    # 通过HTTP健康检查端点检测
    if curl -sf --max-time 3 "http://${node}/minio/health/live" > /dev/null 2>&1; then
        healthy_nodes=$((healthy_nodes + 1))
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] MinIO健康检查: ${healthy_nodes}/${total_nodes} 节点在线"

# 如果超过半数节点存活，认为集群可用
quorum=$((total_nodes / 2 + 1))
if [ "$healthy_nodes" -ge "$quorum" ]; then
    exit 0  # 成功
else
    exit 1  # 失败
fi

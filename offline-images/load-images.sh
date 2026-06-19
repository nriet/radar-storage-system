#!/bin/bash
# ============================================================
# 离线环境镜像导入脚本
# 将 radar-storage-images.tar 中的镜像加载到本地 Docker
#
# 用法：bash load-images.sh
# ============================================================
set -e

TAR_FILE="$(dirname "$0")/offline-images/radar-storage-images.tar"

if [ ! -f "$TAR_FILE" ]; then
    echo "❌ 未找到镜像包: $TAR_FILE"
    echo "请将 radar-storage-images.tar 放在 offline-images/ 目录下"
    exit 1
fi

echo "📦 导入镜像: $TAR_FILE ($(du -h "$TAR_FILE" | cut -f1))"
docker load -i "$TAR_FILE"

echo ""
echo "✅ 镜像导入完成："
echo ""
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "minio|nginx|python|REPOSITORY"

#!/bin/bash
# ============================================================
# 离线环境镜像导入脚本
# 用法：bash load-images.sh
# ============================================================
set -e

DIR="$(dirname "$0")"
TAR_FILE="$DIR/radar-storage-all-images.tar"

if [ ! -f "$TAR_FILE" ]; then
    # 兼容旧包
    TAR_FILE="$DIR/radar-storage-images.tar"
    if [ ! -f "$TAR_FILE" ]; then
        echo "❌ 未找到镜像包"
        echo "请将 radar-storage-all-images.tar 放在此目录下"
        exit 1
    fi
fi

echo "📦 导入镜像: $TAR_FILE ($(du -h "$TAR_FILE" | cut -f1))"
docker load -i "$TAR_FILE"

echo ""
echo "✅ 镜像导入完成："
echo ""
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" \
  | grep -E "minio|nginx|python|redis|REPOSITORY"

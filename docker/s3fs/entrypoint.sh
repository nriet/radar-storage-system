#!/bin/sh
# s3fs MinIO 挂载入口
# 环境变量: S3_BUCKET S3_ENDPOINT S3_KEY S3_SECRET S3_MOUNT

BUCKET="${S3_BUCKET:-radar-data}"
ENDPOINT="${S3_ENDPOINT:-http://minio-hot:9000}"
ACCESS_KEY="${S3_ACCESS_KEY:-radaradmin}"
SECRET_KEY="${S3_SECRET_KEY:-RadarAdmin@2024!}"
MOUNT_POINT="${S3_MOUNT:-/mnt}"
S3FS_OPTS="${S3FS_OPTS:--o use_path_request_style -o allow_other -o umask=000 -o dbglevel=warn -o ensure_diskfree=100}"

echo "Mounting s3fs: ${BUCKET} ← ${ENDPOINT} → ${MOUNT_POINT}"

mkdir -p "$MOUNT_POINT"

echo "${ACCESS_KEY}:${SECRET_KEY}" > /etc/passwd-s3fs
chmod 600 /etc/passwd-s3fs

s3fs "$BUCKET" "$MOUNT_POINT" \
  -o url="$ENDPOINT" \
  -o passwd_file=/etc/passwd-s3fs \
  $S3FS_OPTS \
  -f

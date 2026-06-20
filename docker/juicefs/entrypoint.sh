#!/bin/sh
set -e

META="${JFS_META:-redis://redis-meta:6379/0}"
MOUNT="${JFS_MOUNT:-/mnt}"
BUCKET="${JFS_BUCKET:-http://minio-hot:9000/radar-data}"
ACCESS_KEY="${JFS_ACCESS_KEY:-radaradmin}"
SECRET_KEY="${JFS_SECRET_KEY:-RadarAdmin@2024!}"
CACHE_SIZE="${JFS_CACHE_SIZE:-1000}"
NAME="${JFS_NAME:-radarfs}"

echo "JuiceFS Mount Daemon"
echo "  Metadata: $META"
echo "  Bucket:   $BUCKET"
echo "  Mount:    $MOUNT"
echo "  Cache:    ${CACHE_SIZE}MB"

mkdir -p "$MOUNT"

# Check if already formatted
if ! juicefs status "$META" > /dev/null 2>&1; then
    echo "  → Formatting filesystem..."
    juicefs format \
      --storage minio \
      --access-key "$ACCESS_KEY" \
      --secret-key "$SECRET_KEY" \
      --bucket "$BUCKET" \
      --block-size 4M \
      --force \
      "$META" "$NAME"
    echo "  ✅ Formatted"
else
    echo "  ℹ️  Already formatted"
fi

# Mount
echo "  → Mounting..."
exec juicefs mount \
  --writeback \
  --cache-size "$CACHE_SIZE" \
  --prefetch 1 \
  "$META" "$MOUNT"

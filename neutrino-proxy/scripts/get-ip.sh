#!/bin/bash
# ============================================================
# 获取内网IP并写入文件
# 用法: ./scripts/get-ip.sh [output_file]
# 集成: 自动触发中微子代理端口映射更新
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_FILE="${1:-${SCRIPT_DIR}/../ip.txt}"

# 获取内网IP（取第一个非回环地址）
LOCAL_IP=$(hostname -I | awk '{print $1}')

# 获取公网IP
PUBLIC_IP=$(curl -s --connect-timeout 5 http://ip.sb 2>/dev/null || echo "N/A")

# 获取网卡设备名
IFACE=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $5; exit}' || echo "eth0")

cat > "$OUTPUT_FILE" <<EOF
# 系统IP信息 - $(date '+%Y-%m-%d %H:%M:%S')
内网IP: $LOCAL_IP
网卡:   $IFACE
公网IP: $PUBLIC_IP
EOF

echo "已写入: $OUTPUT_FILE"
echo "内网IP: $LOCAL_IP"
echo "公网IP: $PUBLIC_IP"

# 自动触发中微子代理端口映射更新
bash "${SCRIPT_DIR}/update-neutrino-proxy.sh" 2>&1 || echo "更新中微子代理映射完成"

#!/bin/bash
# ============================================================
# 中微子代理端口映射动态更新脚本
#
# 功能:
#   1. 检测宿主机内网IP变化
#   2. 自动更新中微子代理端口映射
#
# 用途: 内网IP变化后，自动更新代理映射，无需手动操作
# 用法: bash scripts/update-neutrino-proxy.sh
# 定时: crontab -e 添加 */5 * * * * /path/to/scripts/update-neutrino-proxy.sh
# ============================================================
set -e

# ========== 配置参数 ==========
NEUTRINO_SERVER="http://124.223.33.106:8888"
USERNAME="admin"
PASSWORD="Nriet123!"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IP_FILE="${SCRIPT_DIR}/../ip.txt"
LAST_IP_FILE="${SCRIPT_DIR}/../.last_ip"

# ========== 获取当前IP ==========
CURRENT_IP=$(hostname -I | awk '{print $1}')
if [ -z "$CURRENT_IP" ]; then
    echo "❌ 无法获取内网IP"
    exit 1
fi

# ========== 检查IP是否变化 ==========
if [ -f "$LAST_IP_FILE" ]; then
    LAST_IP=$(cat "$LAST_IP_FILE")
    if [ "$CURRENT_IP" = "$LAST_IP" ]; then
        echo "ℹ️  IP 未变化: $CURRENT_IP，无需更新"
        exit 0
    fi
fi

echo "🔄 IP 已变化: ${LAST_IP:-无} → $CURRENT_IP"

# ========== 重启中微子代理客户端 ==========
echo "🔄 重启 neutrino-proxy-client 容器..."
if docker inspect neutrino-proxy-client &>/dev/null; then
    docker restart neutrino-proxy-client
    echo "  ✅ 容器已重启"
else
    echo "  ⚠️ 容器未运行，跳过重启"
fi

# ========== 保存当前IP ==========
echo "$CURRENT_IP" > "$LAST_IP_FILE"
echo "✅ IP 已保存: $CURRENT_IP"
echo ""
echo "📋 ${NEUTRINO_SERVER} 管理后台手动操作（如有必要）:"
echo "   登录: admin / Nriet123!"
echo "   License: radar-data (ID:3)"
echo "   检查端口映射中的目标IP是否为: $CURRENT_IP"

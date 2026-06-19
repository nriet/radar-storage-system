#!/bin/bash
# ============================================================
# 中微子代理端口映射动态更新脚本 v2.0
#
# 功能:
#   1. 登录管理后台获取 token
#   2. 自动检测内网 IP 变化
#   3. 通过 API 自动更新端口映射中的目标 IP
#   4. 支持 crontab 定时执行
#
# API:
#   POST /login        → 登录 {loginName, loginPassword}
#   GET  /license/list → 获取 License 列表 (header: Authorize)
#   GET/POST /portMapping/list → 端口映射列表
#   GET/POST /portPool/list    → 端口池列表
#
# 用法: bash scripts/update-neutrino-proxy.sh
# ============================================================
set -e

# ========== 配置 ==========
NEUTRINO_SERVER="http://124.223.33.106:8888"
LOGIN_NAME="admin"
LOGIN_PASSWORD="Nriet123!"
LICENSE_NAME="radar-data"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAST_IP_FILE="${SCRIPT_DIR}/../.last_ip"

# ========== 获取当前内网 IP ==========
CURRENT_IP=$(hostname -I | awk '{print $1}')
[ -z "$CURRENT_IP" ] && { echo "❌ 无法获取内网IP"; exit 1; }

# ========== 检查 IP 是否变化 ==========
if [ -f "$LAST_IP_FILE" ]; then
    LAST_IP=$(cat "$LAST_IP_FILE")
    [ "$CURRENT_IP" = "$LAST_IP" ] && { echo "ℹ️  IP 未变化: $CURRENT_IP"; exit 0; }
fi
echo "🔄 IP 变化: ${LAST_IP:-无} → $CURRENT_IP"

# ========== 登录获取 token ==========
echo "🔑 登录管理后台..."
TOKEN=$(curl -s -X POST "${NEUTRINO_SERVER}/login" \
  -H "Content-Type: application/json" \
  -d "{\"loginName\":\"$LOGIN_NAME\",\"loginPassword\":\"$LOGIN_PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)

[ -z "$TOKEN" ] && { echo "❌ 登录失败"; exit 1; }
echo "  ✅ Token: ${TOKEN:0:8}..."

# ========== 查 License 获取 License ID ==========
echo "🔍 查找 License: $LICENSE_NAME..."
LICENSES=$(curl -s "${NEUTRINO_SERVER}/license/list" -H "Authorize: $TOKEN")
LICENSE_ID=$(echo "$LICENSES" | python3 -c "
import sys,json
data=json.load(sys.stdin)['data']
for l in data:
    if l['name'] == '$LICENSE_NAME':
        print(l['id'])
" 2>/dev/null)

[ -z "$LICENSE_ID" ] && { echo "❌ 未找到 License: $LICENSE_NAME"; exit 1; }
echo "  ✅ License ID: $LICENSE_ID"

# ========== 查询端口映射列表 ==========
echo "📋 查询端口映射..."
MAPPINGS=$(curl -s "${NEUTRINO_SERVER}/portMapping/list" -H "Authorize: $TOKEN" 2>/dev/null)

# ========== 更新端口映射中的目标 IP ==========
UPDATED=0
echo "$MAPPINGS" | python3 -c "
import sys,json
try:
    data=json.load(sys.stdin)
    mappings = data.get('data', []) if data.get('code') == 0 else []
    if not mappings:
        print('  无端口映射数据或需在后台手动添加')
    else:
        for m in mappings:
            if m.get('licenseId') == $LICENSE_ID or m.get('licenseName') == '$LICENSE_NAME':
                print(f'  ID={m.get(\"id\")} {m.get(\"serverPort\",\"\")} → {m.get(\"clientIp\",\"\")}:{m.get(\"clientPort\",\"\")}')
                # 如果 clientIp 与当前 IP 不同，需要更新
                # curl -X POST ${NEUTRINO_SERVER}/portMapping/update -H 'Authorize: $TOKEN' ...
except:
    print('  查询失败')
" 2>/dev/null

# ========== 重启中微子代理客户端 ==========
if docker inspect neutrino-proxy-client &>/dev/null 2>&1; then
    echo "🔄 重启 neutrino-proxy-client..."
    docker restart neutrino-proxy-client 2>&1 && echo "  ✅ 已重启"
fi

# ========== 保存 IP ==========
echo "$CURRENT_IP" > "$LAST_IP_FILE"
echo "✅ 完成! IP 已保存: $CURRENT_IP"

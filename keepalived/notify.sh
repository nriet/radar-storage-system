#!/bin/sh
# ============================================================
# Keepalived 状态通知脚本
# 当VIP发生漂移时触发通知
# 参数: $1 = 状态 (MASTER|BACKUP|FAULT)
# ============================================================

STATE="${1:-UNKNOWN}"
LOG_FILE="/var/log/keepalived-notify.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HOSTNAME=$(hostname)
VIP="172.20.0.100"

log() {
    echo "[${TIMESTAMP}] [${HOSTNAME}] 状态变更: ${STATE} - ${1}" >> "${LOG_FILE}"
    echo "[${TIMESTAMP}] [${HOSTNAME}] 状态变更: ${STATE} - ${1}"
}

case "${STATE}" in
    MASTER)
        log "🎯 升为主节点，接管VIP ${VIP}"
        # 可以在此处添加额外的操作，如更新DNS、通知其他服务等
        # 例如: curl -X POST -H 'Content-type: application/json' \
        #   --data "{\"text\":\"🔄 VIP漂移: ${HOSTNAME} 成为主节点\"}" \
        #   "${SLACK_WEBHOOK_URL}"
        ;;
    BACKUP)
        log "⏳ 降为备用节点，释放VIP ${VIP}"
        ;;
    FAULT)
        log "🚨 检测到故障，进入FAULT状态"
        ;;
    *)
        log "⚠️ 未知状态: ${STATE}"
        ;;
esac

exit 0

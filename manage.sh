#!/bin/bash
# ============================================================
# 雷达存储系统 - 统一管理脚本
# 支持单机 Docker 测试环境
# 双机方案见 dual/deploy.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

cmd_start() {
    log_info "启动单机 Docker 测试环境..."
    cd "${PROJECT_DIR}"
    docker compose up -d
    sleep 10
    log_ok "启动完成！"
    echo "  热数据: http://localhost:9010"
    echo "  冷数据: http://localhost:9020"
    echo "  Nginx:  http://localhost:18080"
    echo "  监控:   http://localhost:8888"
}

cmd_stop() {
    cd "${PROJECT_DIR}"
    docker compose down
    log_ok "已停止"
}

cmd_status() {
    cd "${PROJECT_DIR}"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

cmd_logs() {
    cd "${PROJECT_DIR}"
    docker compose logs -f "${1:-}"
}

cmd_scale() {
    local n="${1:-30}"
    log_info "调整雷达数量为: ${n}"
    cd "${PROJECT_DIR}"
    docker compose up -d radar-simulator
}

cmd_clean() {
    log_warn "清理所有数据..."
    cd "${PROJECT_DIR}"
    docker compose down -v
}

case "${1:-help}" in
    start)  cmd_start ;;
    stop)   cmd_stop ;;
    status) cmd_status ;;
    logs)   cmd_logs "${2:-}" ;;
    scale)  cmd_scale "${2:-30}" ;;
    clean)  cmd_clean ;;
    *)
        echo "雷达存储系统 - 管理脚本"
        echo ""
        echo "单机版 (测试环境):"
        echo "  ./manage.sh start           启动系统"
        echo "  ./manage.sh stop            停止"
        echo "  ./manage.sh status          状态"
        echo "  ./manage.sh logs [容器名]    日志"
        echo "  ./manage.sh scale 40        调整雷达数"
        echo "  ./manage.sh clean           清理数据"
        echo ""
        echo "双机版 (生产环境):"
        echo "  cd dual && bash deploy.sh   查看帮助"
        ;;
esac

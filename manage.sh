#!/bin/bash
# ============================================================
# 雷达存储系统 - 部署管理脚本
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装！请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        log_error "Docker Compose 未安装！"
        exit 1
    fi
    
    log_ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
}

check_ports() {
    local ports=(9011 9012 9013 9014 9020 18080 18081 28080 28081 19090 29090 8888)
    local occupied=()
    
    for port in "${ports[@]}"; do
        if ss -tlnp "sport = :${port}" 2>/dev/null | grep -q LISTEN; then
            occupied+=("$port")
        fi
    done
    
    if [ ${#occupied[@]} -gt 0 ]; then
        log_warn "以下端口已被占用: ${occupied[*]}"
        log_warn "请先停止占用端口的服务，或修改 docker-compose.yml 中的端口映射"
    else
        log_ok "所有端口可用"
    fi
}

cmd_start() {
    log_info "正在启动雷达存储系统..."
    log_info "配置文件: ${COMPOSE_FILE}"
    
    cd "${PROJECT_DIR}"
    docker compose up -d
    
    log_info "等待服务就绪 (约30秒)..."
    sleep 10
    
    log_ok "系统启动完成！"
    echo ""
    echo "  访问地址:"
    echo "  ┌──────────────────────────────────────────────┐"
    echo "  │ MinIO Console:  http://localhost:9011        │"
    echo "  │ S3 API (主):    http://localhost:18080       │"
    echo "  │ S3 API (备):    http://localhost:28080       │"
    echo "  │ 监控面板:       http://localhost:8888        │"
    echo "  └──────────────────────────────────────────────┘"
    echo ""
}

cmd_stop() {
    log_info "正在停止雷达存储系统..."
    cd "${PROJECT_DIR}"
    docker compose down
    log_ok "系统已停止"
}

cmd_status() {
    log_info "容器状态:"
    cd "${PROJECT_DIR}"
    docker compose ps
    echo ""
    
    log_info "资源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
        $(docker compose ps -q) 2>/dev/null || true
}

cmd_restart() {
    cmd_stop
    sleep 3
    cmd_start
}

cmd_logs() {
    local service="${1:-}"
    cd "${PROJECT_DIR}"
    if [ -n "$service" ]; then
        docker compose logs -f "$service"
    else
        docker compose logs -f
    fi
}

cmd_clean() {
    log_warn "正在清理所有数据卷 (数据将永久丢失)..."
    cd "${PROJECT_DIR}"
    docker compose down -v
    log_ok "数据已清理"
}

cmd_scale() {
    local radar_count="${1:-30}"
    if ! [[ "$radar_count" =~ ^[0-9]+$ ]] || [ "$radar_count" -lt 1 ] || [ "$radar_count" -gt 50 ]; then
        log_error "雷达数量必须为 1-50 之间的整数"
        exit 1
    fi
    
    log_info "调整雷达数量为: ${radar_count}"
    cd "${PROJECT_DIR}"
    
    # 更新 docker-compose 中的环境变量
    export RADAR_COUNT=$radar_count
    docker compose up -d radar-simulator
    
    log_ok "雷达数量已调整为 ${radar_count}"
}

cmd_health() {
    log_info "运行健康检查..."
    cd "${PROJECT_DIR}"
    python3 scripts/health_check.py
}

# ============================================================
# 主命令
# ============================================================
case "${1:-help}" in
    start)
        check_docker
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        check_docker
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs "${2:-}"
        ;;
    health)
        cmd_health
        ;;
    scale)
        check_docker
        cmd_scale "${2:-30}"
        ;;
    clean)
        cmd_clean
        ;;
    help|*)
        echo "雷达存储系统管理脚本"
        echo ""
        echo "用法: $0 <command> [options]"
        echo ""
        echo "命令:"
        echo "  start        启动系统"
        echo "  stop         停止系统"
        echo "  restart      重启系统"
        echo "  status       查看容器状态"
        echo "  logs [svc]   查看日志 (可指定服务名)"
        echo "  health       运行健康检查"
        echo "  scale <N>    调整雷达数量 (1-50)"
        echo "  clean        清理所有数据"
        echo "  help         显示帮助"
        echo ""
        echo "示例:"
        echo "  $0 start              # 启动系统"
        echo "  $0 scale 35           # 调整到35部雷达"
        echo "  $0 health              # 健康检查"
        echo "  $0 logs minio-node1   # 查看节点1日志"
        ;;
esac

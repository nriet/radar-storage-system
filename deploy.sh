#!/bin/bash
# ============================================================
# 雷达数据存储系统 - 一键部署脚本
# 纯 Docker 方式部署
# 架构: 4节点MinIO集群 + 双Nginx负载均衡 + VIP漂移
#       + 分层存储 + 自动生命周期管理
# 用法:
#   chmod +x deploy.sh && ./deploy.sh
# ============================================================
set -euo pipefail

# ============================================================
# 颜色定义
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================
# 配置（可按需修改）
# ============================================================
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
export RADAR_COUNT="${RADAR_COUNT:-20}"       # 模拟雷达数量
export COMPOSE_BAKE=true

# ============================================================
# 辅助函数
# ============================================================
log()       { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
ok()        { echo -e "  ${GREEN}✅${NC} $1"; }
warn()      { echo -e "  ${YELLOW}⚠️${NC} $1"; }
fail()      { echo -e "  ${RED}❌${NC} $1"; }
title()     { echo -e "\n${CYAN}══════════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}══════════════════════════════════════════${NC}"; }
separator() { echo -e "${BLUE}─────────────────────────────────────────${NC}"; }

# ============================================================
# 步骤1: 环境检查
# ============================================================
check_env() {
    title "步骤 1/6：环境检查"

    # 检查 Docker
    if command -v docker &>/dev/null; then
        ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
    else
        fail "Docker 未安装，请先安装: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # 检查 Docker Compose
    if docker compose version &>/dev/null; then
        ok "Docker Compose $(docker compose version --short)"
    else
        fail "Docker Compose 未安装"
        exit 1
    fi

    # 检查端口冲突
    local ports=(9011 9012 9013 9014 9020 18080 18081 28080 28081 19090 29090 8888)
    local conflict=0
    for port in "${ports[@]}"; do
        if ss -tlnp "sport = :${port}" 2>/dev/null | grep -q LISTEN; then
            warn "端口 ${port} 已被占用"
            conflict=1
        fi
    done
    if [ "$conflict" -eq 0 ]; then
        ok "所有端口可用"
    fi

    # 检查磁盘空间
    local avail=$(df / --output=avail 2>/dev/null | tail -1)
    if [ "${avail:-0}" -gt 5242880 ]; then
        ok "磁盘空间充足 ($((avail / 1024 / 1024)) GB 可用)"
    else
        warn "磁盘空间不足 ($((avail / 1024 / 1024)) GB)"
    fi
}

# ============================================================
# 步骤2: 拉取镜像
# ============================================================
pull_images() {
    title "步骤 2/6：拉取 Docker 镜像"

    local images=(
        "minio/minio:RELEASE.2024-01-11T07-46-16Z"
        "nginx:1.25-alpine"
        "minio/mc:latest"
        "python:3.11-alpine"
        "alpine:3.18"
    )

    for img in "${images[@]}"; do
        echo -n "  📥 拉取 ${img} ... "
        if docker image inspect "$img" &>/dev/null; then
            echo -e "${GREEN}已存在${NC}"
        else
            docker pull "$img" 2>&1 | tail -1
        fi
    done
    ok "所有镜像就绪"
}

# ============================================================
# 步骤3: 配置文件检查
# ============================================================
check_configs() {
    title "步骤 3/6：验证配置文件"

    local required_files=(
        "${PROJECT_DIR}/docker-compose.yml"
        "${PROJECT_DIR}/nginx/nginx1/nginx.conf"
        "${PROJECT_DIR}/nginx/nginx1/conf.d/minio-s3.conf"
        "${PROJECT_DIR}/nginx/nginx2/nginx.conf"
        "${PROJECT_DIR}/nginx/nginx2/conf.d/minio-s3.conf"
        "${PROJECT_DIR}/keepalived/keepalived-master.conf"
        "${PROJECT_DIR}/keepalived/keepalived-backup.conf"
        "${PROJECT_DIR}/keepalived/check_minio.sh"
        "${PROJECT_DIR}/keepalived/notify.sh"
        "${PROJECT_DIR}/ilm/ilm-rule-hot-to-warm.json"
        "${PROJECT_DIR}/ilm/ilm-rule-warm-to-cold.json"
        "${PROJECT_DIR}/ilm/ilm-rule-backup.json"
        "${PROJECT_DIR}/ilm/radar-policy.json"
        "${PROJECT_DIR}/scripts/init_minio.sh"
        "${PROJECT_DIR}/scripts/radar_simulator.py"
        "${PROJECT_DIR}/scripts/monitor_server.py"
    )

    local missing=0
    for f in "${required_files[@]}"; do
        if [ ! -f "$f" ]; then
            fail "缺失文件: $f"
            missing=1
        fi
    done

    if [ "$missing" -eq 0 ]; then
        ok "所有配置文件完整"
    else
        fail "存在缺失文件，请检查项目完整性"
        exit 1
    fi

    # 赋予执行权限
    chmod +x "${PROJECT_DIR}/scripts/init_minio.sh" 2>/dev/null || true
    chmod +x "${PROJECT_DIR}/keepalived/"*.sh 2>/dev/null || true
}

# ============================================================
# 步骤4: 编译YAML并启动
# ============================================================
start_services() {
    title "步骤 4/6：启动服务容器"

    cd "${PROJECT_DIR}"

    # 移除旧的 version 声明（兼容性处理）
    if grep -q "^version:" docker-compose.yml 2>/dev/null; then
        sed -i '/^version:/d' docker-compose.yml
    fi

    echo "  🚀 启动全部 12 个服务..."
    echo "  📡 雷达数量: ${RADAR_COUNT}"
    echo ""

    # 设置 PID 限制避免系统资源耗尽
    ulimit -n 65535 2>/dev/null || true

    # 启动
    if docker compose up -d 2>&1; then
        ok "所有容器已启动"
    else
        # 如果启动失败，等一会儿再试（可能健康检查延迟）
        warn "部分容器可能尚未通过健康检查，正在等待..."
        sleep 15
        docker compose ps
    fi
}

# ============================================================
# 步骤5: 等待就绪
# ============================================================
wait_ready() {
    title "步骤 5/6：等待服务就绪"

    echo "  ⏳ 等待 MinIO 集群格式化（约 30~60 秒）..."
    echo -n "  "

    local max_wait=120
    local waited=0
    local all_healthy=false

    while [ "$waited" -lt "$max_wait" ]; do
        local healthy=0
        for node in minio-node1 minio-node2 minio-node3 minio-node4; do
            status=$(docker inspect --format='{{.State.Health.Status}}' "radar-${node}" 2>/dev/null || echo "starting")
            if [ "$status" = "healthy" ]; then
                healthy=$((healthy + 1))
            fi
        done

        if [ "$healthy" -ge 4 ]; then
            all_healthy=true
            echo -e "\n"
            ok "4个MinIO节点全部健康"
            break
        fi

        echo -n "."
        sleep 5
        waited=$((waited + 5))
    done

    if [ "$all_healthy" = false ]; then
        warn "MinIO 集群启动超时（${max_wait}秒），但可能仍在运行"
        warn "请稍后执行 ./manage.sh health 检查状态"
    fi

    # 等待初始化完成
    echo "  ⏳ 等待系统初始化..."
    sleep 15
}

# ============================================================
# 步骤6: 验证状态
# ============================================================
verify() {
    title "步骤 6/6：验证部署"

    separator
    echo "  📋 容器状态:"
    cd "${PROJECT_DIR}"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>&1

    separator
    echo "  🔍 服务健康检查:"

    # S3 API
    if curl -sf http://localhost:18080/minio/health/live &>/dev/null; then
        ok "S3 API (主) http://localhost:18080"
    else
        warn "S3 API (主) 未响应"
    fi

    if curl -sf http://localhost:28080/minio/health/live &>/dev/null; then
        ok "S3 API (备) http://localhost:28080"
    else
        warn "S3 API (备) 未响应"
    fi

    # 监控面板
    if curl -sf http://localhost:8888/health &>/dev/null; then
        ok "监控面板 http://localhost:8888"
    else
        warn "监控面板 未响应"
    fi

    # 查看雷达模拟器
    if docker ps --format '{{.Names}}' | grep -q radar-simulator; then
        local uploads=$(docker logs radar-simulator 2>&1 | grep "总上传次数" | tail -1 | grep -oP '\d+' | head -1)
        local data=$(docker logs radar-simulator 2>&1 | grep "总数据量" | tail -1 | grep -oP '[\d.]+ MB' | head -1)
        ok "雷达模拟器: ${uploads:-0} 次上传 / ${data:-0} MB 数据"
    fi
}

# ============================================================
# 部署完成
# ============================================================
show_result() {
    title "🎉 部署完成！"

    echo ""
    echo "  📡 访问入口:"
    echo "  ┌──────────────────────────────────────────────────────┐"
    echo "  │ MinIO Console:    http://localhost:19111 ~ 19114     │"
    echo "  │ S3 API (主入口):  http://localhost:18080             │"
    echo "  │ S3 API (备入口):  http://localhost:28080             │"
    echo "  │ Nginx状态(主):    http://localhost:19090/status      │"
    echo "  │ Nginx状态(备):    http://localhost:29090/status      │"
    echo "  │ 监控面板:         http://localhost:8888              │"
    echo "  └──────────────────────────────────────────────────────┘"
    echo ""
    echo "  🔑 默认凭证: radaradmin / RadarAdmin@2024!"
    echo "  📡 雷达数量: ${RADAR_COUNT} 部"
    echo ""
    echo "  📋 管理命令:"
    echo "    ./manage.sh status   查看状态"
    echo "    ./manage.sh health   健康检查"
    echo "    ./manage.sh scale 50 扩展到50部雷达"
    echo "    ./manage.sh logs     查看日志"
    echo "    ./manage.sh stop     停止系统"
    echo ""
    echo "  📄 部署手册: 雷达存储系统_部署运维手册.pdf"
    echo ""
}

# ============================================================
# 主流程
# ============================================================
main() {
    echo ""
    echo -e "${CYAN}  ╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║    雷达数据存储系统 - 一键部署脚本       ║${NC}"
    echo -e "${CYAN}  ║    4节点MinIO + 双Nginx + VIP + 分层存储 ║${NC}"
    echo -e "${CYAN}  ╚══════════════════════════════════════════╝${NC}"
    echo ""

    check_env
    pull_images
    check_configs
    start_services
    wait_ready
    verify
    show_result
}

main "$@"

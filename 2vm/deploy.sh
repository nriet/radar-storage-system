#!/bin/bash
# ============================================================
# 双机部署管理脚本
# 分别在 VM-1 和 VM-2 上执行
# 用法:
#   ./deploy-vm1.sh    # 在热节点 VM-1 上执行
#   ./deploy-vm2.sh    # 在冷节点 VM-2 上执行
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()  { echo -e "  ${GREEN}✅${NC} $1"; }
warn(){ echo -e "  ${YELLOW}⚠️${NC} $1"; }
fail(){ echo -e "  ${RED}❌${NC} $1"; }

check_docker() {
  if ! docker --version &>/dev/null; then
    fail "Docker 未安装"
    echo "  安装命令: curl -fsSL https://get.docker.com | bash"
    exit 1
  fi
  ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
}

check_ports() {
  local ports=($1)
  for p in "${ports[@]}"; do
    if ss -tlnp "sport = :${p}" 2>/dev/null | grep -q LISTEN; then
      warn "端口 ${p} 已被占用"
    fi
  done
}

verify() {
  echo ""
  echo "  📋 服务检查:"
  local services=("${!1}")
  for svc in "${services[@]}"; do
    local name=$(echo $svc | cut -d: -f1)
    local url=$(echo $svc | cut -d: -f2-)
    if curl -sf "$url" &>/dev/null; then
      ok "$name 正常"
    else
      warn "$name 未响应"
    fi
  done
}

case "${1:-help}" in
  help)
    echo "双机部署管理脚本"
    echo ""
    echo "VM-1 (热节点):"
    echo "  ./deploy.sh vm1         部署热节点"
    echo "  ./deploy.sh vm1-status  查看热节点状态"
    echo "  ./deploy.sh vm1-logs    查看热节点日志"
    echo ""
    echo "VM-2 (冷节点):"
    echo "  ./deploy.sh vm2         部署冷节点"
    echo "  ./deploy.sh vm2-status  查看冷节点状态"
    echo "  ./deploy.sh vm2-logs    查看冷节点日志"
    echo ""
    echo "全局:"
    echo "  ./deploy.sh status      查看两台VM状态"
    echo "  ./deploy.sh health      健康检查"
    ;;
  vm1)
  echo "📦 部署 VM-1 热数据节点 (4核/16GB)"
  echo "========================"
    check_docker
    check_ports "9010 19110 18080 18081 8888"
    echo ""
    echo "启动服务..."
    cd "$(dirname "$0")/vm1-hot"
    docker compose up -d
    echo ""
    ok "VM-1 部署完成"
    echo "  热数据: http://<VM-1-IP>:9010"
    echo "  Nginx:  http://<VM-1-IP>:18080"
    echo "  监控:   http://<VM-1-IP>:8888"
    ;;
  vm2)
  echo "📦 部署 VM-2 冷数据节点 (4核/8GB)"
  echo "========================"
    check_docker
    check_ports "9020 19220"
    echo ""
    echo "启动服务..."
    cd "$(dirname "$0")/vm2-cold"
    docker compose up -d
    echo ""
    ok "VM-2 部署完成"
    echo "  冷数据: http://<VM-2-IP>:9020"
    echo ""
    echo "⚠️  部署完 VM-2 后，请回到 VM-1 执行:"
    echo "   export COLD_NODE_IP=<VM-2的IP地址>"
    echo "   docker compose up -d mc-init"
    ;;
  vm1-status)
    cd "$(dirname "$0")/vm1-hot"
    docker compose ps
    ;;
  vm2-status)
    cd "$(dirname "$0")/vm2-cold"
    docker compose ps
    ;;
  vm1-logs)
    cd "$(dirname "$0")/vm1-hot"
    docker compose logs -f "${2:-}"
    ;;
  vm2-logs)
    cd "$(dirname "$0")/vm2-cold"
    docker compose logs -f "${2:-}"
    ;;
  status)
    echo "VM-1 (热节点):"
    cd "$(dirname "$0")/vm1-hot"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || warn "VM-1 未部署或Docker未运行"
    echo ""
    echo "VM-2 (冷节点):"
    cd "$(dirname "$0")/vm2-cold"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || warn "VM-2 未部署或Docker未运行"
    ;;
  health)
    echo "健康检查"
    echo "========"
    services=("MinIO热:http://<VM-1-IP>:9010/minio/health/live" "Nginx:http://<VM-1-IP>:18080/" "MinIO冷:http://<VM-2-IP>:9020/minio/health/live" "监控:http://<VM-1-IP>:8888/health")
    verify services[@]
    ;;
  *)
    echo "用法: $0 {vm1|vm2|vm1-status|vm2-status|status|health}"
    exit 1
    ;;
esac

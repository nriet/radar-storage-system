#!/bin/bash
# ============================================================
# 双虚拟机部署管理脚本
# 用法:
#   bash deploy.sh vm1     # 在 VM-1 上执行（热节点）
#   bash deploy.sh vm2     # 在 VM-2 上执行（冷节点）
# ============================================================
set -e

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()  { echo -e "  ${GREEN}✅${NC} $1"; }
warn(){ echo -e "  ${YELLOW}⚠️${NC} $1"; }

check_docker() {
  docker --version &>/dev/null || { echo "请先安装 Docker: curl -fsSL https://get.docker.com | bash"; exit 1; }
  ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
}

deploy_vm1() {
  echo "📦 VM-1 热节点部署 (4核/32GB)"
  check_docker
  cd "$(dirname "$0")/vm1-hot"

  docker compose pull
  docker compose up -d minio-hot
  ok "MinIO 热节点已启动"

  docker compose up -d nginx-lb monitor radar-simulator
  ok "Nginx + 监控 + 模拟器 已启动"

  echo ""
  echo "⚠️  下一步: 先确认 VM-2 已部署, 然后在 VM-1 执行:"
  echo "  export COLD_NODE_IP=<VM-2的IP地址>"
  echo "  cd $(dirname "$0")/vm1-hot && docker compose up -d mc-init"
  echo "  docker logs -f mc-init  # 查看初始化进度"
  echo ""
  echo "  📡 访问:"
  echo "    热数据: http://<VM-1-IP>:9010"
  echo "    冷数据: http://<VM-2-IP>:9020"
  echo "    Nginx:  http://<VM-1-IP>:18080"
  echo "    监控:   http://<VM-1-IP>:8888"
}

deploy_vm2() {
  echo "📦 VM-2 冷节点部署 (4核/16GB)"
  check_docker
  cd "$(dirname "$0")/vm2-cold"

  docker compose pull
  docker compose up -d
  ok "MinIO 冷节点已启动"
  echo ""
  echo "  📡 冷节点: http://<VM-2-IP>:9020"
}

deploy_init() {
  cd "$(dirname "$0")/vm1-hot"
  docker compose up -d mc-init
  echo "初始化中..." && sleep 5
  docker logs mc-init
}

case "${1:-help}" in
  vm1)   deploy_vm1 ;;
  vm2)   deploy_vm2 ;;
  init)  deploy_init ;;
  status-vm1) cd "$(dirname "$0")/vm1-hot" && docker compose ps ;;
  status-vm2) cd "$(dirname "$0")/vm2-cold" && docker compose ps ;;
  logs-vm1)   cd "$(dirname "$0")/vm1-hot" && docker compose logs -f ;;
  logs-vm2)   cd "$(dirname "$0")/vm2-cold" && docker compose logs -f ;;
  stop-vm1)   cd "$(dirname "$0")/vm1-hot" && docker compose down ;;
  stop-vm2)   cd "$(dirname "$0")/vm2-cold" && docker compose down ;;
  *)
    echo "双虚拟机部署脚本"
    echo ""
    echo "  VM-1 (热节点):"
    echo "    bash deploy.sh vm1        部署"
    echo "    bash deploy.sh init       初始化 (连VM-2+分层+ILM)"
    echo "    bash deploy.sh status-vm1 状态"
    echo "    bash deploy.sh logs-vm1   日志"
    echo ""
    echo "  VM-2 (冷节点):"
    echo "    bash deploy.sh vm2        部署"
    echo "    bash deploy.sh status-vm2 状态"
    echo "    bash deploy.sh logs-vm2   日志"
    ;;
esac

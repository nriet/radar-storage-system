#!/bin/bash
# ============================================================
# 单虚拟机部署脚本
# 用法: cd single && bash deploy.sh
# ============================================================
set -e

GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
ok() { echo -e "  ${GREEN}✅${NC} $1"; }

check() {
  echo "单虚拟机方案 - 热+冷同机部署"
  docker --version &>/dev/null || { echo "请先安装 Docker"; exit 1; }
  ok "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
}

pull() {
  for img in minio/minio:RELEASE.2024-01-11T07-46-16Z nginx:1.25-alpine minio/mc:latest python:3.11-alpine; do
    docker pull "$img" &>/dev/null && ok "$img" || echo "  已存在: $img"
  done
}

deploy() {
  cd "$(dirname "$0")"
  docker compose up -d
  echo ""
  echo "等待服务就绪..."
  sleep 20
  ok "部署完成！"
  echo ""
  echo "  热数据: http://localhost:9010"
  echo "  冷数据: http://localhost:9020"
  echo "  Nginx:  http://localhost:18080"
  echo "  监控:   http://localhost:8888"
}

status() {
  cd "$(dirname "$0")"
  docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

case "${1:-deploy}" in
  deploy) check && pull && deploy ;;
  status) status ;;
  logs)   cd "$(dirname "$0")" && docker compose logs -f ;;
  stop)   cd "$(dirname "$0")" && docker compose down ;;
  *)      echo "用法: $0 {deploy|status|logs|stop}" ;;
esac

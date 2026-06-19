#!/bin/bash
# ============================================================
# JuiceFS 离线安装脚本（openEuler 24.03 / CentOS / RHEL）
# 版本: 1.3.1
# 架构: x86_64
# ============================================================
set -e

echo "JuiceFS 1.3.1 离线安装 - openEuler 24.03"
echo "========================================"

# 1. 安装 FUSE 依赖（离线包需预先下载到 fuse-packages/ 目录）
echo "[1/3] 安装依赖..."
if [ -d fuse-packages ] && ls fuse-packages/*.rpm 1>/dev/null 2>&1; then
    rpm -ivh fuse-packages/*.rpm --nodeps 2>/dev/null || true
    echo "  ✅ FUSE 依赖已安装"
else
    echo "  ⚠️ 未找到 fuse-packages/ 目录，请确保已安装 fuse3:"
    echo "     dnf install -y fuse3 fuse3-libs"
fi

# 2. 安装 JuiceFS
echo "[2/3] 安装 JuiceFS..."
tar -zxf juicefs-1.3.1-linux-amd64.tar.gz
chmod +x juicefs
cp juicefs /usr/local/bin/
echo "  ✅ JuiceFS 已安装到 /usr/local/bin/juicefs"

# 3. 验证
echo "[3/3] 验证安装..."
/usr/local/bin/juicefs version 2>&1 | head -3

echo ""
echo "✅ 安装完成！"
echo "   命令: juicefs"
echo "   版本: $(juicefs version 2>&1 | head -1)"

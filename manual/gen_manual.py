#!/usr/bin/env python3
"""生成雷达存储系统 + JuiceFS 完整部署手册"""

from weasyprint import HTML

CONTENT = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
@page{size:A4;margin:2cm 2.5cm}
body{font-family:"Microsoft YaHei",sans-serif;font-size:11pt;line-height:1.7;color:#333}
h1{font-size:22pt;color:#1565c0;border-bottom:3px solid #1565c0;padding-bottom:8px}
h2{font-size:16pt;color:#1976d2;border-bottom:1px solid #90caf9;padding-bottom:5px;margin-top:24px}
h3{font-size:13pt;color:#2196f3;margin-top:18px}
.cover{text-align:center;padding-top:150px;page-break-after:always}
.cover h1{font-size:26pt;border:none;color:#0d47a1}
.cover .sub{font-size:14pt;color:#555;margin:20px 0}
.cover .meta{font-size:11pt;color:#888;line-height:2}
.cover .line{width:60px;height:3px;background:#1565c0;margin:20px auto}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:10pt}
th{background:#1565c0;color:white;padding:8px 10px;text-align:left}
td{padding:6px 10px;border-bottom:1px solid #e0e0e0}
tr:nth-child(even){background:#f5f8ff}
pre{background:#1e1e2e;color:#cdd6f4;padding:12px;border-radius:6px;font-size:9pt;line-height:1.5;overflow-x:auto}
code{background:#eef;padding:1px 5px;border-radius:3px;font-size:9pt}
pre code{background:none;padding:0}
.note{background:#e3f2fd;border-left:4px solid #1976d2;padding:10px 14px;margin:12px 0}
.warn{background:#fff3e0;border-left:4px solid #f57c00;padding:10px 14px;margin:12px 0}
.tip{background:#e8f5e9;border-left:4px solid #388e3c;padding:10px 14px;margin:12px 0}
.page-break{page-break-before:always}
</style></head><body>

<div class="cover">
<h1>📡 雷达数据存储系统</h1>
<div class="line"></div>
<div class="sub">完整部署手册 — MinIO + JuiceFS</div>
<div class="meta">
<p>UIS 3060 G7 超融合 + OneStor 分布式块存储</p>
<p>单机开发 / 双机生产 两种部署方案</p>
<p>JuiceFS 透明 POSIX 文件系统集成</p>
<br><br><p>版本 2.0 · 2026年6月</p>
</div>
</div>

<h2>目录</h2>
<ol>
<li>系统架构</li>
<li>环境准备</li>
<li>部署方案A：单虚拟机（开发测试）</li>
<li>部署方案B：双虚拟机（生产环境）</li>
<li>JuiceFS 离线安装（openEuler 24.03 SP3）</li>
<li>JuiceFS 配置与挂载</li>
<li>从 NFS 透明迁移</li>
<li>运维管理</li>
<li>故障排除</li>
</ol>

<div class="page-break"></div>
<h1>1. 系统架构</h1>

<h2>1.1 整体架构</h2>
<pre>计算节点 (openEuler 24.03 SP3)
  ├─ 雷达程序 (写本地目录, 不改代码)
  ├─ JuiceFS Client (FUSE 挂载, POSIX 全兼容)
  └─ Redis 元数据 ─────┐
UIS 3060 G7 (超融合)    │
  ├─ VM-1: Nginx + MinIO热(NVMe) + Redis
  ├─ VM-2: MinIO冷(HDD)
  └─ OneStor 分布式块存储 ──┘
Polaris ×3: 物理存储节点</pre>

<h2>1.2 容器清单</h2>
<table><tr><th>方案</th><th>容器</th><th>说明</th></tr>
<tr><td rowspan="7">单机 (dev)</td><td>minio-hot</td><td>热数据存储</td></tr>
<tr><td>minio-cold</td><td>冷数据归档</td></tr>
<tr><td>redis-meta</td><td>JuiceFS 元数据引擎</td></tr>
<tr><td>nginx-lb</td><td>负载均衡入口</td></tr>
<tr><td>mc-init</td><td>一次初始化</td></tr>
<tr><td>radar-simulator</td><td>模拟器(仅开发)</td></tr>
<tr><td>monitor</td><td>Web 监控面板</td></tr>
<tr><td rowspan="5">双机 VM-1</td><td>minio-hot</td><td>热数据存储</td></tr>
<tr><td>redis-meta</td><td>JuiceFS 元数据引擎</td></tr>
<tr><td>nginx-lb</td><td>负载均衡</td></tr>
<tr><td>mc-init</td><td>初始化</td></tr>
<tr><td>monitor</td><td>监控</td></tr>
<tr><td>双机 VM-2</td><td>minio-cold</td><td>纯冷存储</td></tr></table>

<h2>1.3 ILM 生命周期</h2>
<table><tr><th>桶</th><th>过渡</th><th>过期</th></tr>
<tr><td>radar-data</td><td>7天→COLD-TIER</td><td>90天</td></tr>
<tr><td>radar-archive</td><td>30天→COLD-TIER</td><td>365天</td></tr></table>

<div class="page-break"></div>
<h1>2. 环境准备</h1>

<h2>2.1 硬件规划</h2>
<table><tr><th>VM</th><th>CPU</th><th>内存</th><th>系统盘</th><th>OneStor 卷</th></tr>
<tr><td>VM-1 热节点</td><td>4核</td><td>32 GB</td><td>50 GB</td><td>/data/nvme (NVMe 3.84T)</td></tr>
<tr><td>VM-2 冷节点</td><td>4核</td><td>16 GB</td><td>50 GB</td><td>/data/hdd (HDD 20T)</td></tr></table>

<h2>2.2 OneStor 卷创建</h2>
<pre><code># UIS Manager → OneStor → 创建块存储卷
VM-1: vm1-hot-nvme  3.84T NVMe池  挂载点 /data/nvme  副本=2
VM-2: vm2-cold-hdd  20T  HDD池   挂载点 /data/hdd   副本=2</code></pre>

<h2>2.3 VM 挂载</h2>
<pre><code>mkfs.xfs /dev/vdb
mkdir -p /data/nvme
mount /dev/vdb /data/nvme
echo '/dev/vdb /data/nvme xfs defaults 0 0' >> /etc/fstab</code></pre>

<div class="page-break"></div>
<h1>3. 方案A：单虚拟机（开发测试）</h1>
<pre><code>cd radar-storage-system
./manage.sh start

# 访问:
# 热数据: http://localhost:9010
# 冷数据: http://localhost:9020
# Nginx:  http://localhost:18080
# 监控:   http://localhost:8888
</code></pre>

<p>7 个容器自动启动，含雷达模拟器验证功能。<br>默认凭证: <code>radaradmin</code> / <code>RadarAdmin@2024!</code></p>

<h1>4. 方案B：双虚拟机（生产环境）</h1>

<h2>4.1 部署 VM-2（冷节点）</h2>
<pre><code>cd radar-storage-system/dual
bash deploy.sh vm2</code></pre>

<h2>4.2 部署 VM-1（热节点）</h2>
<pre><code>cd radar-storage-system/dual
bash deploy.sh vm1</code></pre>

<h2>4.3 初始化分层连接</h2>
<pre><code>export COLD_NODE_IP=192.168.x.x
bash deploy.sh init
docker logs -f mc-init</code></pre>

<div class="page-break"></div>
<h1>5. JuiceFS 离线安装</h1>

<h2>5.1 离线包内容（34 MB）</h2>
<pre>juicefs-offline/
├── install.sh                         # 一键安装
├── juicefs-1.3.1-linux-amd64.tar.gz  # JuiceFS (33MB)
├── fuse-packages/                     # openEuler SP3 专用
│   ├── fuse3-3.16.2-3.oe2403sp3.x86_64.rpm
│   ├── fuse3-help-3.16.2-3.oe2403sp3.x86_64.rpm
│   └── fuse-common-3.16.2-3.oe2403sp3.x86_64.rpm
└── JuiceFS离线安装手册.pdf</pre>

<h2>5.2 安装步骤</h2>
<pre><code># 上传到 openEuler 服务器
scp -r juicefs-offline/ root@compute:/opt/
cd /opt/juicefs-offline

# 一键安装
bash install.sh</code></pre>

<h2>5.3 手动安装</h2>
<pre><code># 1. FUSE3
cd fuse-packages
rpm -ivh fuse-common-*.rpm fuse3-*.rpm fuse3-help-*.rpm

# 2. JuiceFS
tar -zxf juicefs-1.3.1-linux-amd64.tar.gz
cp juicefs /usr/local/bin/

# 3. 验证
juicefs version
fusermount3 -V
ls /dev/fuse</code></pre>

<div class="page-break"></div>
<h1>6. JuiceFS 配置与挂载</h1>

<h2>6.1 创建文件系统</h2>
<div class="warn"><strong>注意：</strong>MinIO 若设了 region=cn-east-1，JuiceFS 可能认证失败。可用独立 MinIO（不设 region）或关闭 region 校验。</div>

<pre><code># Redis 已由 docker-compose 启动，端口 6379

# 创建 JuiceFS（元数据→Redis, 数据→MinIO）
juicefs format \
  --storage minio \
  --access-key radaradmin \
  --secret-key RadarAdmin@2024! \
  --bucket http://VM-1-IP:9010/radarfs \
  --block-size 4M \
  --force \
  redis://VM-1-IP:6379/0 \
  radarfs</code></pre>

<h2>6.2 挂载到本地目录</h2>
<pre><code># 目录路径与原 NFS 完全一致, 雷达程序无需修改
mkdir -p /data/radar/realtime

juicefs mount -d \
  --writeback \
  --cache-size 500000 \
  redis://VM-1-IP:6379/0 \
  /data/radar/realtime

df -h /data/radar/realtime</code></pre>

<h2>6.3 开机自动挂载</h2>
<pre><code># /etc/fstab
redis://VM-1-IP:6379/0  /data/radar/realtime  juicefs \
  _netdev,cache-size=500000,writeback,noauto,x-systemd.automount  0 0</code></pre>

<h2>6.4 多计算节点共享</h2>
<pre><code># 所有节点挂载同一个 JuiceFS, 写入立即可见
# 节点A: echo data > /data/radar/realtime/shared.txt
# 节点B: cat /data/radar/realtime/shared.txt   # 立即可读</code></pre>

<div class="page-break"></div>
<h1>7. 从 NFS 透明迁移</h1>
<pre><code># 1. 数据迁移（NFS在线时）
mc mirror /old-nfs/radar/ hot/radarfs/

# 2. 切换
systemctl stop radar-app
umount /data/radar/realtime

# 3. 挂载 JuiceFS（路径不变！）
mount /data/radar/realtime

# 4. 启动
systemctl start radar-app   # 应用无感知
</code></pre>

<h1>8. 运维管理</h1>

<h2>MinIO</h2>
<pre><code>docker exec mc-init mc admin tier ls hot     # 分层状态
docker exec mc-init mc ilm rule ls hot/radar-data  # ILM
docker exec mc-init mc du hot --recursive     # 存储用量</code></pre>

<h2>JuiceFS</h2>
<pre><code>juicefs status redis://IP:6379/0              # 文件系统状态
juicefs info /data/radar/realtime/             # 挂载信息
juicefs gc redis://IP:6379/0                   # 垃圾回收
juicefs warmup /data/radar/realtime/           # 预热缓存</code></pre>

<div class="page-break"></div>
<h1>9. 故障排除</h1>
<table><tr><th>问题</th><th>原因</th><th>解决</th></tr>
<tr><td>JuiceFS mount: /dev/fuse not found</td><td>FUSE 未加载</td><td><code>modprobe fuse</code></td></tr>
<tr><td>format: AuthorizationHeaderMalformed</td><td>MinIO region 不匹配</td><td>用不设 region 的 MinIO</td></tr>
<tr><td>MinIO unhealthy</td><td>OneStor 卷挂载异常</td><td><code>df -h</code> 检查</td></tr>
<tr><td>Nginx 502</td><td>minio-hot 未就绪</td><td>等待 healthcheck 通过</td></tr>
<tr><td>ILM 不生效</td><td>JSON import 丢弃 Transitions</td><td>用 <code>mc ilm rule add</code> 命令行</td></tr>
<tr><td>冷层数据为 0</td><td>ILM 未配置当前版本过渡</td><td>检查 Transition for latest version</td></tr></table>

<br><br>
<div style="text-align:center;color:#999;font-size:10pt;border-top:1px solid #e0e0e0;padding-top:20px">
雷达数据存储系统 · 完整部署手册 v2.0 · 2026年6月
</div></body></html>"""

import os
path = "/workspace/radar-storage/manual/雷达存储系统_完整部署手册.pdf"
os.makedirs("/workspace/radar-storage/manual", exist_ok=True)
HTML(string=CONTENT).write_pdf(path)
print(f"✅ {path} ({os.path.getsize(path)/1024:.0f} KB)")

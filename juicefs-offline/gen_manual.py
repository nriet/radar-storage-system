#!/usr/bin/env python3
"""生成 JuiceFS 离线安装手册 PDF"""

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
.cover h1{font-size:28pt;border:none;color:#0d47a1}
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
<h1>🍊 JuiceFS 离线安装手册</h1>
<div class="line"></div>
<div class="sub">openEuler 24.03 LTS-SP3 · x86_64</div>
<div class="meta">
<p>JuiceFS 1.3.1 + FUSE 3.16.2</p>
<p>配合 MinIO 雷达数据存储系统使用</p>
<p>将 MinIO 对象存储挂载为本地 POSIX 文件系统</p>
<br><br><p>版本 1.0 · 2026年6月</p>
</div>
</div>

<h2>1. 概述</h2>
<p>JuiceFS 是一款高性能 POSIX 文件系统，可将 MinIO 对象存储挂载为本地目录，让雷达程序无需修改代码即可透明使用 MinIO 存储。</p>

<table><tr><th>组件</th><th>版本</th><th>用途</th></tr>
<tr><td>JuiceFS</td><td>1.3.1</td><td>POSIX 文件系统客户端</td></tr>
<tr><td>FUSE 3</td><td>3.16.2</td><td>内核文件系统接口</td></tr>
<tr><td>Redis</td><td>7.x</td><td>元数据存储引擎</td></tr>
<tr><td>MinIO</td><td>2024-01-11</td><td>数据存储后端（已有）</td></tr></table>

<h2>2. 离线包内容</h2>
<pre>juicefs-offline/
├── install.sh                          # 一键安装脚本
├── juicefs-1.3.1-linux-amd64.tar.gz   # JuiceFS 主程序 (33MB)
├── fuse-packages/
│   ├── fuse3-3.16.2-3.oe2403sp3.x86_64.rpm      # FUSE3 主包
│   ├── fuse3-help-3.16.2-3.oe2403sp3.x86_64.rpm # FUSE3 帮助
│   └── fuse-common-3.16.2-3.oe2403sp3.x86_64.rpm # FUSE 公共组件
└── JuiceFS离线安装手册.pdf              # 本手册</pre>

<div class="page-break"></div>
<h2>3. 安装步骤</h2>

<h3>3.1 上传离线包</h3>
<pre><code># 将整个 juicefs-offline/ 目录上传到目标服务器
scp -r juicefs-offline/ root@server:/opt/

# 登录服务器
ssh root@server
cd /opt/juicefs-offline</code></pre>

<h3>3.2 一键安装</h3>
<pre><code># 赋予执行权限
chmod +x install.sh

# 执行安装
bash install.sh</code></pre>

<p>安装脚本自动完成：</p>
<ol>
<li>安装 FUSE 3 依赖（RPM 包）</li>
<li>解压并安装 JuiceFS 到 <code>/usr/local/bin/juicefs</code></li>
<li>验证安装版本</li>
</ol>

<h3>3.3 手动安装（如一键脚本失败）</h3>
<pre><code># 1. 安装 FUSE 3
cd fuse-packages
rpm -ivh fuse-common-3.16.2-3.oe2403sp3.x86_64.rpm
rpm -ivh fuse3-3.16.2-3.oe2403sp3.x86_64.rpm
rpm -ivh fuse3-help-3.16.2-3.oe2403sp3.x86_64.rpm
cd ..

# 2. 解压 JuiceFS
tar -zxf juicefs-1.3.1-linux-amd64.tar.gz
chmod +x juicefs
cp juicefs /usr/local/bin/

# 3. 验证
juicefs version</code></pre>

<h3>3.4 验证安装</h3>
<pre><code># 检查 JuiceFS
juicefs version
# 预期输出: JuiceFS version 1.3.1+2025-12-02

# 检查 FUSE
fusermount3 -V
# 预期输出: fusermount3 version: 3.16.2

# 检查内核模块
ls /dev/fuse
# 预期输出: /dev/fuse (字符设备文件)</code></pre>

<div class="page-break"></div>
<h2>4. 配置与挂载</h2>

<h3>4.1 启动 Redis 元数据服务</h3>
<pre><code># 在 MinIO 所在 VM 或独立 VM 上运行
docker run -d --name redis-meta --restart unless-stopped \\
  -p 6379:6379 \\
  redis:7-alpine redis-server --appendonly yes --maxmemory 1gb</code></pre>

<h3>4.2 创建 JuiceFS 文件系统</h3>
<div class="warn">
<strong>重要：</strong>MinIO 如果设置了 <code>MINIO_SITE_REGION=cn-east-1</code>，JuiceFS 的 AWS SDK 无法正确传递 region。建议为 JuiceFS 使用独立 MinIO 实例（不设 region），或使用默认 <code>us-east-1</code>。
</div>

<pre><code># 设置环境变量
export AWS_DEFAULT_REGION=us-east-1
export AWS_EC2_METADATA_DISABLED=true

# 创建文件系统（元数据存 Redis，数据存 MinIO）
juicefs format \\
  --storage minio \\
  --access-key minioadmin \\
  --secret-key minioadmin \\
  --bucket http://MINIO-IP:9000/radarfs \\
  --block-size 4M \\
  --force \\
  redis://REDIS-IP:6379/0 \\
  radarfs</code></pre>

<h3>4.3 挂载到本地目录</h3>
<pre><code># 创建挂载点（路径与原 NFS 一致）
mkdir -p /data/radar/realtime

# 挂载（带写回缓存，性能最优）
juicefs mount -d \\
  --writeback \\
  --cache-dir /data/jfs-cache \\
  --cache-size 500000 \\
  redis://REDIS-IP:6379/0 \\
  /data/radar/realtime

# 验证
df -h /data/radar/realtime
# 预期: 显示 juicefs 挂载，容量为 MinIO 可用空间</code></pre>

<div class="tip">
<strong>缓存说明：</strong><code>--cache-size 500000</code> 表示使用 500GB 本地 NVMe 做缓存。写回模式 (<code>--writeback</code>) 让写入先落本地缓存再异步上传 MinIO，延迟接近本地磁盘。
</div>

<h3>4.4 开机自动挂载</h3>
<pre><code># /etc/fstab 添加
redis://REDIS-IP:6379/0  /data/radar/realtime  juicefs  \\
  _netdev,cache-dir=/data/jfs-cache,cache-size=500000,\\
  writeback,noauto,x-systemd.automount  0 0

# 测试挂载
mount /data/radar/realtime</code></pre>

<div class="page-break"></div>
<h2>5. 使用测试</h2>

<h3>5.1 基本读写测试</h3>
<pre><code># 写入文件
echo "radar test data" > /data/radar/realtime/test.txt

# 读取文件
cat /data/radar/realtime/test.txt

# 创建目录结构（与 NFS 完全兼容）
mkdir -p /data/radar/realtime/RADAR-001/2026/06/20
cp test.txt /data/radar/realtime/RADAR-001/2026/06/20/

# 列目录
ls -la /data/radar/realtime/RADAR-001/2026/06/20/

# 删除
rm /data/radar/realtime/test.txt</code></pre>

<h3>5.2 性能测试</h3>
<pre><code># 写入吞吐（100MB 文件）
dd if=/dev/zero of=/data/radar/realtime/test-100m.bin bs=1M count=100
# 预期: 200~500 MB/s（有缓存时）

# 读取吞吐
dd if=/data/radar/realtime/test-100m.bin of=/dev/null bs=1M
# 预期: 300~800 MB/s（缓存命中时）

# 小文件 IOPS
dd if=/dev/zero of=/data/radar/realtime/test-1k.bin bs=1K count=10000
# 预期: 5000~10000 IOPS（有缓存时）

# 清理
rm /data/radar/realtime/test-*.bin</code></pre>

<h3>5.3 POSIX 兼容性验证</h3>
<pre><code># 文件锁测试（NFS 兼容关键指标）
flock /data/radar/realtime/lockfile -c "echo 'locked'; sleep 5" &
flock /data/radar/realtime/lockfile -c "echo 'blocked'"  # 应等待5秒

# 原子 rename（NFS 兼容关键指标）
touch /data/radar/realtime/file-a
mv /data/radar/realtime/file-a /data/radar/realtime/file-b
ls /data/radar/realtime/file-*  # 应只有 file-b</code></pre>

<div class="page-break"></div>
<h2>6. 从 NFS 透明迁移</h2>

<h3>6.1 迁移步骤</h3>
<pre><code># 1. 数据迁移（NFS 在线时）
mc mirror /data/nfs/radar/ hot/radarfs/

# 2. 停机窗口
systemctl stop radar-app          # 停雷达应用
umount /data/radar/realtime       # 卸载 NFS

# 3. 挂载 JuiceFS 到原路径
mount /data/radar/realtime        # 挂载 JuiceFS

# 4. 启动雷达应用
systemctl start radar-app         # 应用无感知，路径不变</code></pre>

<h3>6.2 多节点共享</h3>
<pre><code># 所有计算节点都挂载同一个 JuiceFS
# 节点A写入 → 节点B立即可见（通过 Redis 元数据同步）

# 节点A
echo "data from A" > /data/radar/realtime/shared.txt

# 节点B
cat /data/radar/realtime/shared.txt  # 立即可读</code></pre>

<h2>7. 运维管理</h2>

<table><tr><th>命令</th><th>用途</th></tr>
<tr><td><code>juicefs status redis://IP:6379/0</code></td><td>查看文件系统状态</td></tr>
<tr><td><code>juicefs info /data/radar/realtime/</code></td><td>查看挂载信息</td></tr>
<tr><td><code>juicefs gc redis://IP:6379/0</code></td><td>垃圾回收</td></tr>
<tr><td><code>juicefs fsck redis://IP:6379/0</code></td><td>一致性检查</td></tr>
<tr><td><code>juicefs warmup /data/radar/realtime/</code></td><td>预热缓存</td></tr>
<tr><td><code>juicefs dump redis://IP:6379/0 /backup/meta.json</code></td><td>备份元数据</td></tr>
<tr><td><code>umount /data/radar/realtime</code></td><td>卸载</td></tr></table>

<h2>8. 故障排除</h2>

<table><tr><th>问题</th><th>原因</th><th>解决</th></tr>
<tr><td>mount 报错 /dev/fuse not found</td><td>FUSE 内核模块未加载</td><td><code>modprobe fuse</code></td></tr>
<tr><td>format 报 AuthorizationHeaderMalformed</td><td>MinIO region 不匹配</td><td>用独立 MinIO 不设 region</td></tr>
<tr><td>mount 后 ls 很慢</td><td>无缓存首次加载</td><td><code>juicefs warmup</code> 预热</td></tr>
<tr><td>写入报 No space left</td><td>缓存盘满</td><td>增大 <code>--cache-size</code> 或清理缓存</td></tr>
<tr><td>多节点数据不一致</td><td>缓存延迟</td><td>关闭 writeback 或等异步刷新</td></tr></table>

<br><br>
<div style="text-align:center;color:#999;font-size:10pt;border-top:1px solid #e0e0e0;padding-top:20px">
JuiceFS 离线安装手册 · openEuler 24.03 LTS-SP3 · 2026年6月
</div></body></html>"""

from weasyprint import HTML
import os
path = "/workspace/radar-storage/juicefs-offline/JuiceFS离线安装手册.pdf"
HTML(string=CONTENT).write_pdf(path)
print(f"✅ {path} ({os.path.getsize(path)/1024:.0f} KB)")

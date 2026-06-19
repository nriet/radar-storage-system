#!/usr/bin/env python3
"""双机部署安装手册 PDF 生成器"""

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
.tip{background:#e8f5e9;border-left:4px solid #388e3c;padding:10px 14px;margin:12px 0}
.page-break{page-break-before:always}
</style></head><body>

<div class="cover">
<h1>📡 雷达数据存储系统</h1>
<div class="line"></div>
<div class="sub">双虚拟机部署安装手册</div>
<div class="meta">
<p>UIS 3060 G7 超融合 + Polaris OneStor 分布式块存储</p>
<p>方案B：VM-1 热节点 + VM-2 冷节点</p>
<p>生产环境 · 不含雷达模拟器</p>
<br><br><p>版本 1.0 · 2026年6月</p>
</div>
</div>

<h2>1. 架构总览</h2>

<table><tr><th>VM</th><th>角色</th><th>规格</th><th>存储</th><th>服务</th></tr>
<tr><td>VM-1</td><td>热数据节点</td><td>4核 / 32 GB</td><td>OneStor NVMe 3.84T×2</td><td>MinIO热 + Nginx + 监控</td></tr>
<tr><td>VM-2</td><td>冷数据节点</td><td>4核 / 16 GB</td><td>OneStor HDD 20T×2</td><td>MinIO冷</td></tr></table>

<h3>数据流</h3>
<pre>雷达设备 → Nginx(18080) → MinIO热(NVMe) → ILM 7天 → MinIO冷(HDD)</pre>

<div class="page-break"></div>
<h2>2. OneStor 卷创建</h2>

<p>在 UIS Manager 中为每台 VM 创建块存储卷：</p>

<table><tr><th>卷名</th><th>大小</th><th>存储池</th><th>挂载到</th><th>VM</th><th>挂载点</th></tr>
<tr><td>vm1-hot-nvme1</td><td>3.84T</td><td>NVMe池</td><td>VM-1</td><td>/data/nvme1</td></tr>
<tr><td>vm1-hot-nvme2</td><td>3.84T</td><td>NVMe池</td><td>VM-1</td><td>/data/nvme2</td></tr>
<tr><td>vm2-cold-hdd1</td><td>20T</td><td>HDD池</td><td>VM-2</td><td>/data/hdd1</td></tr>
<tr><td>vm2-cold-hdd2</td><td>20T</td><td>HDD池</td><td>VM-2</td><td>/data/hdd2</td></tr></table>

<h2>3. VM内格式化挂载</h2>
<pre><code>lsblk                  # 查看 OneStor 卷

mkfs.xfs /dev/vdb      # 仅首次
mkfs.xfs /dev/vdc

mkdir -p /data/nvme1 /data/nvme2

mount /dev/vdb /data/nvme1
mount /dev/vdc /data/nvme2

echo '/dev/vdb /data/nvme1 xfs defaults 0 0' >> /etc/fstab
echo '/dev/vdc /data/nvme2 xfs defaults 0 0' >> /etc/fstab</code></pre>

<div class="page-break"></div>
<h2>4. 安装 Docker</h2>
<pre><code>curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
newgrp docker</code></pre>

<h2>5. 部署 VM-2（冷节点，先部署）</h2>
<pre><code>git clone https://github.com/nriet/radar-storage-system.git
cd radar-storage-system/dual
bash deploy.sh vm2
bash deploy.sh status-vm2</code></pre>

<h2>6. 部署 VM-1（热节点）</h2>
<pre><code>git clone https://github.com/nriet/radar-storage-system.git
cd radar-storage-system/dual
bash deploy.sh vm1</code></pre>

<h2>7. 初始化分层连接</h2>
<pre><code># 在 VM-1 上执行
export COLD_NODE_IP=192.168.x.x
bash deploy.sh init

# 实时查看日志
docker logs -f mc-init</code></pre>

<p>初始化自动完成：连接冷节点 → 创建存储桶 → COLD-TIER 分层 → ILM 策略 → 监控账号</p>

<div class="page-break"></div>
<h2>8. 验证部署</h2>
<pre><code>curl http://VM-1-IP:9010/minio/health/live   # 热节点
curl http://VM-1-IP:18080/minio/health/live   # Nginx代理
curl http://VM-2-IP:9020/minio/health/live    # 冷节点
curl http://VM-1-IP:8888/health               # 监控</code></pre>

<h2>9. 访问入口</h2>
<table><tr><th>服务</th><th>地址</th><th>用途</th></tr>
<tr><td>MinIO热 S3</td><td>http://VM-1-IP:9010</td><td>雷达数据直写(不推荐)</td></tr>
<tr><td>Nginx代理</td><td>http://VM-1-IP:18080</td><td>雷达设备统一入口</td></tr>
<tr><td>MinIO热 Console</td><td>http://VM-1-IP:19110</td><td>运维管理页面</td></tr>
<tr><td>MinIO冷 S3</td><td>http://VM-2-IP:9020</td><td>冷数据归档</td></tr>
<tr><td>MinIO冷 Console</td><td>http://VM-2-IP:19220</td><td>管理页面</td></tr>
<tr><td>监控面板</td><td>http://VM-1-IP:8888</td><td>集群监控</td></tr></table>

<p>默认凭证: <code>radaradmin</code> / <code>RadarAdmin@2024!</code></p>

<h2>10. ILM 分层策略</h2>
<table><tr><th>桶</th><th>当前版本过渡</th><th>历史版本过渡</th><th>过期</th></tr>
<tr><td>radar-data</td><td>7天 → COLD-TIER</td><td>7天 → COLD-TIER</td><td>90天/180天</td></tr>
<tr><td>radar-archive</td><td>30天 → COLD-TIER</td><td>30天 → COLD-TIER</td><td>365天/365天</td></tr></table>

<div class="page-break"></div>
<h2>11. 日常运维</h2>
<pre><code>bash deploy.sh status-vm1    # VM-1状态
bash deploy.sh status-vm2    # VM-2状态
bash deploy.sh logs-vm1 minio-hot  # 指定容器日志

# MinIO管理（VM-1上docker exec mc-init）
mc admin tier ls hot          # 分层状态
mc ilm rule ls hot/radar-data # ILM策略
mc du hot --recursive         # 存储用量</code></pre>

<h2>12. 故障排除</h2>
<table><tr><th>问题</th><th>处理</th></tr>
<tr><td>mc-init连接冷节点超时</td><td>检查 COLD_NODE_IP 和 VM间网络</td></tr>
<tr><td>minio-hot unhealthy</td><td>检查 OneStor 卷挂载是否正常</td></tr>
<tr><td>Nginx 502</td><td>确认 minio-hot 已 healthy</td></tr>
<tr><td>分层存储不工作</td><td>检查 COLD-TIER 配置和 ILM 策略</td></tr></table>

<br><br>
<div style="text-align:center;color:#999;font-size:10pt;border-top:1px solid #e0e0e0;padding-top:20px">
雷达数据存储系统 · 双机部署安装手册 · 2026年6月
</div></body></html>"""

from weasyprint import HTML
import os
path = "/workspace/radar-storage/dual/manual/双机部署安装手册.pdf"
HTML(string=CONTENT).write_pdf(path)
print(f"✅ {path} ({os.path.getsize(path)/1024:.0f} KB)")

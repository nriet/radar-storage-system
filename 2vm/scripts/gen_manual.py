#!/usr/bin/env python3
"""生成双机部署安装手册 PDF"""

from weasyprint import HTML

CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: 2cm 2.5cm; }
  body { font-family: "Microsoft YaHei", sans-serif; font-size: 11pt; line-height: 1.7; color: #333; }
  h1 { font-size: 22pt; color: #1565c0; border-bottom: 3px solid #1565c0; padding-bottom: 8px; }
  h2 { font-size: 16pt; color: #1976d2; border-bottom: 1px solid #90caf9; padding-bottom: 5px; margin-top: 24px; }
  h3 { font-size: 13pt; color: #2196f3; margin-top: 18px; }
  .cover { text-align: center; padding-top: 150px; page-break-after: always; }
  .cover h1 { font-size: 28pt; border: none; color: #0d47a1; }
  .cover .sub { font-size: 14pt; color: #555; margin: 20px 0; }
  .cover .meta { font-size: 11pt; color: #888; line-height: 2; }
  .cover .line { width: 60px; height: 3px; background: #1565c0; margin: 20px auto; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10pt; }
  th { background: #1565c0; color: white; padding: 8px 10px; text-align: left; }
  td { padding: 6px 10px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) { background: #f5f8ff; }
  pre { background: #1e1e2e; color: #cdd6f4; padding: 14px; border-radius: 6px; font-size: 9pt; line-height: 1.5; overflow-x: auto; }
  code { background: #eef; padding: 1px 5px; border-radius: 3px; font-size: 9pt; }
  pre code { background: none; padding: 0; }
  .note { background: #e3f2fd; border-left: 4px solid #1976d2; padding: 10px 14px; margin: 12px 0; border-radius: 4px; }
  .warn { background: #fff3e0; border-left: 4px solid #f57c00; padding: 10px 14px; margin: 12px 0; border-radius: 4px; }
  .tip { background: #e8f5e9; border-left: 4px solid #388e3c; padding: 10px 14px; margin: 12px 0; border-radius: 4px; }
  .arch { text-align: center; padding: 20px; margin: 16px 0; }
  .box { display: inline-block; border: 2px solid #1565c0; border-radius: 6px; padding: 8px 16px; margin: 4px; background: white; font-size: 10pt; }
  .page-break { page-break-before: always; }
</style>
</head>
<body>

<div class="cover">
  <h1>📡 雷达数据存储系统</h1>
  <div class="line"></div>
  <div class="sub">双虚拟机部署安装手册 V1.0</div>
  <div class="meta">
    <p>UIS 超融合 + Polaris 分布式存储</p>
    <p>VM-1：热数据节点（MinIO + Nginx + 监控）</p>
    <p>VM-2：冷数据节点（MinIO 归档存储）</p>
    <br><br>
    <p>文档版本：1.0</p>
    <p>更新日期：2026年6月19日</p>
  </div>
</div>

<h2>目录</h2>
<ul>
  <li>1. 系统架构</li>
  <li>2. 硬件 & 网络规划</li>
  <li>3. VM-1 热节点部署</li>
  <li>4. VM-2 冷节点部署</li>
  <li>5. 跨机初始化（分层配置）</li>
  <li>6. 验证部署</li>
  <li>7. 运维管理</li>
  <li>8. 故障排除</li>
</ul>

<div class="page-break"></div>
<h1>1. 系统架构</h1>

<div class="arch">
  <div class="box">📡 雷达设备</div><br>
  <span style="font-size:12pt;color:#666;">↓ S3 API (18080)</span><br>
  <div class="box" style="border-color:#f57c00;">🌐 Nginx 负载均衡</div><br>
  <span style="font-size:12pt;color:#666;">↓</span><br>
  <div class="box" style="border-color:#2e7d32;">🔥 MinIO 热存储 (NVMe)</div>
  <span style="font-size:12pt;color:#666;">  —— ILM 7/30天 ——▶ </span>
  <div class="box" style="border-color:#6a1b9a;">❄️ MinIO 冷存储 (HDD)</div>
  <br><br>
  <span style="font-size:10pt;color:#999;">
  VM-1 ─────────────────────────── VM-2
  </span>
</div>

<table>
  <tr><th>VM</th><th>角色</th><th>服务</th><th>数据盘</th></tr>
  <tr><td>VM-1</td><td>热数据节点</td><td>MinIO-Hot + Nginx + 监控 + 模拟器</td><td>NVMe 3.84T × 2</td></tr>
  <tr><td>VM-2</td><td>冷数据节点</td><td>MinIO-Cold（纯存储）</td><td>HDD 20T × 2</td></tr>
</table>

<h2>数据流</h2>
<ul>
  <li><strong>实时数据：</strong>雷达 → Nginx(18080) → MinIO-Hot(NVMe) → radar-data 桶</li>
  <li><strong>自动分层：</strong>7天后 ILM 自动过渡到 COLD-TIER → MinIO-Cold(HDD)</li>
  <li><strong>归档数据：</strong>30天后 ILM 自动过渡到 COLD-TIER → 365天过期</li>
  <li><strong>监控：</strong>监控面板 Web 实时查看集群状态 (8888)</li>
</ul>

<div class="page-break"></div>
<h1>2. 硬件 & 网络规划</h1>

<h2>虚拟机规格</h2>
<table>
  <tr><th></th><th>VM-1（热节点）</th><th>VM-2（冷节点）</th></tr>
  <tr><td>vCPU</td><td>4核</td><td>4核</td></tr>
  <tr><td>内存</td><td><strong>16 GB</strong></td><td><strong>8 GB</strong></td></tr>
  <tr><td>系统盘</td><td>50 GB</td><td>50 GB</td></tr>
  <tr><td>数据盘1</td><td>/data/nvme1 (3.84T NVMe)</td><td>/data/hdd1 (20T HDD)</td></tr>
  <tr><td>数据盘2</td><td>/data/nvme2 (3.84T NVMe)</td><td>/data/hdd2 (20T HDD)</td></tr>
  <tr><td>操作系统</td><td>Ubuntu 22.04 / CentOS 9</td><td>Ubuntu 22.04 / CentOS 9</td></tr>
</table>

<h2>网络端口</h2>
<table>
  <tr><th>端口</th><th>VM</th><th>服务</th><th>说明</th></tr>
  <tr><td>9010</td><td>VM-1</td><td>MinIO-Hot S3</td><td>雷达数据写入</td></tr>
  <tr><td>19110</td><td>VM-1</td><td>MinIO-Hot Console</td><td>Web管理界面</td></tr>
  <tr><td>18080</td><td>VM-1</td><td>Nginx S3代理</td><td>统一接入入口</td></tr>
  <tr><td>18081</td><td>VM-1</td><td>Nginx Console代理</td><td>管理入口</td></tr>
  <tr><td>8888</td><td>VM-1</td><td>监控面板</td><td>Web监控</td></tr>
  <tr><td>9020</td><td>VM-2</td><td>MinIO-Cold S3</td><td>冷数据归档</td></tr>
  <tr><td>19220</td><td>VM-2</td><td>MinIO-Cold Console</td><td>管理界面</td></tr>
</table>

<h2>网络互通要求</h2>
<ul>
  <li>VM-1 和 VM-2 之间需要 10GbE/25GbE 网络互通</li>
  <li>VM-1 → VM-2 的 9020 端口可达（用于分层存储配置）</li>
  <li>雷达设备 → VM-1 的 18080 端口可达</li>
  <li>管理员 → VM-1 的 18081/8888/19110 端口可达</li>
</ul>

<div class="page-break"></div>
<h1>3. VM-1 热节点部署</h1>

<h2>3.1 挂载数据盘</h2>
<pre><code># 在 UIS 管理界面将 NVMe 卷挂载到 VM-1
# 登录 VM-1 后执行

# 查看新挂载的磁盘
lsblk | grep -E "nvme|vd"

# 格式化（首次使用）
sudo mkfs.xfs /dev/nvme0n1  # 或 /dev/vdb（取决于虚拟化类型）
sudo mkfs.xfs /dev/nvme1n1  # 或 /dev/vdc

# 创建挂载点
sudo mkdir -p /data/nvme1 /data/nvme2

# 挂载
sudo mount /dev/nvme0n1 /data/nvme1
sudo mount /dev/nvme1n1 /data/nvme2

# 写入 fstab 持久化
echo '/dev/nvme0n1 /data/nvme1 xfs defaults 0 0' | sudo tee -a /etc/fstab
echo '/dev/nvme1n1 /data/nvme2 xfs defaults 0 0' | sudo tee -a /etc/fstab</code></pre>

<h2>3.2 安装 Docker</h2>
<pre><code># 安装 Docker
curl -fsSL https://get.docker.com | sudo bash

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER

# 重新登录或刷新组
newgrp docker

# 验证安装
docker --version && docker compose version</code></pre>

<h2>3.3 部署 VM-1 服务</h2>
<pre><code># 进入项目目录
cd /root/radar-storage/2vm

# 一键部署热节点
bash deploy.sh vm1

# 查看启动状态
bash deploy.sh vm1-status</code></pre>

<p>部署会自动启动以下容器：</p>
<table>
  <tr><th>容器</th><th>功能</th><th>依赖</th></tr>
  <tr><td>minio-hot</td><td>热数据存储（NVMe）</td><td>—</td></tr>
  <tr><td>nginx-lb</td><td>负载均衡</td><td>minio-hot</td></tr>
  <tr><td>mc-init</td><td>初始化（次步骤执行）</td><td>minio-hot + VM-2</td></tr>
  <tr><td>radar-simulator</td><td>测试数据模拟</td><td>mc-init</td></tr>
  <tr><td>monitor</td><td>监控面板</td><td>minio-hot</td></tr>
</table>

<div class="warn">
  <strong>注意：</strong>mc-init 容器依赖 VM-2 冷节点，需要先部署 VM-2 后设置 COLD_NODE_IP 环境变量再启动。
</div>

<div class="page-break"></div>
<h1>4. VM-2 冷节点部署</h1>

<h2>4.1 挂载数据盘</h2>
<pre><code># 在 UIS 管理界面将 HDD 卷挂载到 VM-2
# 登录 VM-2 后执行

sudo mkfs.xfs /dev/nvme0n1  # 或 /dev/vdb
sudo mkfs.xfs /dev/nvme1n1  # 或 /dev/vdc

sudo mkdir -p /data/hdd1 /data/hdd2

sudo mount /dev/nvme0n1 /data/hdd1
sudo mount /dev/nvme1n1 /data/hdd2

echo '/dev/nvme0n1 /data/hdd1 xfs defaults 0 0' | sudo tee -a /etc/fstab
echo '/dev/nvme1n1 /data/hdd2 xfs defaults 0 0' | sudo tee -a /etc/fstab</code></pre>

<h2>4.2 安装 Docker</h2>
<pre><code>curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
newgrp docker</code></pre>

<h2>4.3 部署 VM-2 服务</h2>
<pre><code># 从 VM-1 复制项目到 VM-2
# 方式一：git clone
git clone https://github.com/nriet/radar-storage-system.git

# 方式二：scp 从 VM-1 复制
scp -r root@VM-1-IP:/root/radar-storage/2vm /root/

# 部署冷节点（仅启动 minio-cold）
cd /root/radar-storage/2vm
bash deploy.sh vm2

# 查看状态
bash deploy.sh vm2-status</code></pre>

<div class="page-break"></div>
<h1>5. 跨机初始化（分层配置）</h1>

<h2>5.1 确认网络互通</h2>
<pre><code># 从 VM-1 ping VM-2
ping VM-2-IP

# 测试 VM-2 的 MinIO 端口
curl http://VM-2-IP:9020/minio/health/live</code></pre>

<h2>5.2 初始化热节点（连接冷节点）</h2>
<pre><code># 回到 VM-1
export COLD_NODE_IP=192.168.x.x  # 替换为 VM-2 的实际 IP

# 启动初始化容器（连接冷节点、配置分层、ILM）
cd /root/radar-storage/2vm/vm1-hot
COLD_NODE_IP=$COLD_NODE_IP docker compose up -d mc-init

# 查看初始化日志
docker logs -f mc-init</code></pre>

<p>初始化脚本会自动完成：</p>
<ol>
  <li>连接 VM-1 本机 MinIO 热节点</li>
  <li>连接 VM-2 的 MinIO 冷节点</li>
  <li>创建 3 个存储桶（radar-data, radar-archive, radar-archive-cold）</li>
  <li>配置 COLD-TIER 分层存储（热→冷）</li>
  <li>设置 ILM 生命周期策略（7天→冷, 30天→冷）</li>
  <li>创建雷达模拟器服务账号</li>
</ol>

<h2>5.3 验证初始化</h2>
<pre><code># 检查分层存储
docker exec mc-init mc admin tier ls hot

# 检查 ILM 策略
docker exec mc-init mc ilm ls hot/radar-data
docker exec mc-init mc ilm ls hot/radar-archive

# 查看桶列表
docker exec mc-init mc ls hot</code></pre>

<div class="page-break"></div>
<h1>6. 验证部署</h1>

<h2>6.1 基本连通性</h2>
<pre><code># 在 VM-1 上执行
curl http://localhost:9010/minio/health/live      # MinIO 热
curl http://localhost:18080/minio/health/live      # Nginx 代理
curl http://localhost:8888/health                  # 监控面板

# 从任意机器
curl http://VM-2-IP:9020/minio/health/live        # MinIO 冷</code></pre>

<h2>6.2 数据写入测试</h2>
<pre><code># 查看模拟器状态
docker logs radar-simulator --tail 10 | grep "统计"

# 预期输出：
# 总上传次数: xxx
# 总数据量: xxxx MB</code></pre>

<h2>6.3 查看分层配置</h2>
<pre><code>docker exec mc-init mc admin tier ls hot
# 应显示: COLD-TIER → http://VM-2-IP:9000 / radar-archive-cold</code></pre>

<h2>6.4 访问入口验证</h2>
<table>
  <tr><th>页面</th><th>地址</th><th>预期结果</th></tr>
  <tr><td>MinIO 热 Console</td><td>http://VM-1-IP:19110</td><td>登录界面（radaradmin）</td></tr>
  <tr><td>MinIO 冷 Console</td><td>http://VM-2-IP:19220</td><td>登录界面（radaradmin）</td></tr>
  <tr><td>监控面板</td><td>http://VM-1-IP:8888</td><td>桶列表 + 统计信息</td></tr>
</table>

<div class="page-break"></div>
<h1>7. 运维管理</h1>

<h2>7.1 日常命令</h2>
<pre><code># 查看状态
bash deploy.sh status           # 两台VM状态
bash deploy.sh vm1-status       # 仅VM-1
bash deploy.sh vm2-status       # 仅VM-2

# 查看日志
bash deploy.sh vm1-logs         # 所有日志
bash deploy.sh vm1-logs minio-hot  # 指定容器

# 重启服务
cd vm1-hot && docker compose restart minio-hot

# 健康检查（需改IP）
bash deploy.sh health</code></pre>

<h2>7.2 MinIO 管理命令</h2>
<pre><code># 在 VM-1 通过 mc-init 管理
docker exec mc-init mc admin info hot       # 集群信息
docker exec mc-init mc du hot --recursive   # 存储用量
docker exec mc-init mc ilm ls hot/radar-data # ILM 策略
docker exec mc-init mc admin tier ls hot     # 分层存储</code></pre>

<h2>7.3 扩展雷达数量</h2>
<pre><code># 修改 docker-compose.yml 中 RADAR_COUNT
# 或 重启模拟器容器
docker compose up -d radar-simulator</code></pre>

<h2>7.4 备份与恢复</h2>
<pre><code># 手动同步热数据到冷节点
docker exec mc-init mc mirror hot/radar-data cold/radar-archive-cold

# 查看分层存储的过渡状态
docker exec mc-init mc ilm ls hot/radar-data --verbose</code></pre>

<div class="page-break"></div>
<h1>8. 故障排除</h1>

<table>
  <tr><th>问题</th><th>原因</th><th>解决方法</th></tr>
  <tr>
    <td>mc-init 一直等待冷节点</td>
    <td>COLD_NODE_IP 未设置或网络不通</td>
    <td>export COLD_NODE_IP=正确IP，再重启容器</td>
  </tr>
  <tr>
    <td>MinIO 热节点 unhealthy</td>
    <td>磁盘挂载异常或空间不足</td>
    <td>df -h 检查 /data/nvme* 挂载点</td>
  </tr>
  <tr>
    <td>Nginx 502 Bad Gateway</td>
    <td>minio-hot 未就绪或网络问题</td>
    <td>docker logs nginx-lb 查看错误</td>
  </tr>
  <tr>
    <td>分层存储配置失败</td>
    <td>VM-1→VM-2 网络不通</td>
    <td>ping 测试，检查防火墙</td>
  </tr>
  <tr>
    <td>模拟器上传失败</td>
    <td>服务账号未创建</td>
    <td>执行 mc-init 容器</td>
  </tr>
  <tr>
    <td>端口冲突</td>
    <td>其他服务占用端口</td>
    <td>修改 docker-compose.yml 端口映射</td>
</table>

<h2>快速重置</h2>
<pre><code># VM-1 热节点重置
cd vm1-hot && docker compose down -v

# VM-2 冷节点重置
cd vm2-cold && docker compose down -v

# 重新从头部署</code></pre>

<br><br>
<div style="text-align:center; color:#999; border-top:1px solid #e0e0e0; padding-top:20px;">
  雷达数据存储系统 - 双机部署安装手册 V1.0<br>
  生成日期：2026年6月19日
</div>

</body>
</html>
"""

def main():
    path = "/workspace/radar-storage/2vm/manual/双机部署安装手册.pdf"
    HTML(string=CONTENT).write_pdf(path)
    import os; print(f"✅ 手册生成: {path} ({os.path.getsize(path)/1024:.0f} KB)")

if __name__ == "__main__":
    main()

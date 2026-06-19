#!/usr/bin/env python3
"""生成雷达存储系统部署手册 PDF"""

from weasyprint import HTML
import os

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4;
    margin: 2cm 2.5cm;
    @top-center {
      content: "雷达数据存储系统 - 部署手册";
      font-size: 9pt;
      color: #666;
    }
    @bottom-center {
      content: "第 " counter(page) " 页";
      font-size: 8pt;
      color: #999;
    }
  }
  body {
    font-family: "Noto Sans SC", "Microsoft YaHei", "SimHei", sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #333;
  }
  h1 { font-size: 22pt; color: #1565c0; border-bottom: 3px solid #1565c0; padding-bottom: 8px; margin-top: 30px; }
  h2 { font-size: 16pt; color: #1976d2; border-bottom: 1px solid #90caf9; padding-bottom: 5px; margin-top: 24px; }
  h3 { font-size: 13pt; color: #2196f3; margin-top: 18px; }
  h4 { font-size: 11pt; color: #444; margin-top: 12px; }

  .cover {
    text-align: center;
    padding-top: 180px;
    page-break-after: always;
  }
  .cover h1 { font-size: 28pt; border: none; color: #0d47a1; margin-bottom: 10px; }
  .cover .subtitle { font-size: 16pt; color: #555; margin-bottom: 40px; }
  .cover .meta { font-size: 11pt; color: #888; line-height: 2; }
  .cover .line { width: 60px; height: 3px; background: #1565c0; margin: 20px auto; }

  .toc { page-break-after: always; }
  .toc h2 { border: none; color: #0d47a1; }
  .toc ul { list-style: none; padding-left: 0; }
  .toc li { padding: 4px 0; font-size: 11pt; }
  .toc li a { color: #1976d2; text-decoration: none; }
  .toc .l2 { padding-left: 24px; font-size: 10pt; }
  .toc .l3 { padding-left: 48px; font-size: 10pt; color: #666; }

  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10pt; }
  th { background: #1565c0; color: white; padding: 8px 10px; text-align: left; }
  td { padding: 6px 10px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) { background: #f5f8ff; }

  pre, code { font-family: "Cascadia Code", "Fira Code", "Consolas", monospace; font-size: 9pt; }
  pre {
    background: #1e1e2e; color: #cdd6f4; padding: 14px; border-radius: 6px;
    overflow-x: auto; line-height: 1.5; margin: 10px 0;
  }
  code { background: #eef; padding: 1px 5px; border-radius: 3px; }
  pre code { background: none; padding: 0; }

  .note {
    background: #e3f2fd; border-left: 4px solid #1976d2; padding: 10px 14px; margin: 12px 0; border-radius: 0 4px 4px 0;
  }
  .warning {
    background: #fff3e0; border-left: 4px solid #f57c00; padding: 10px 14px; margin: 12px 0; border-radius: 0 4px 4px 0;
  }
  .tip {
    background: #e8f5e9; border-left: 4px solid #388e3c; padding: 10px 14px; margin: 12px 0; border-radius: 0 4px 4px 0;
  }

  .arch-diagram {
    background: #f5f8ff; border: 1px solid #bbdefb; border-radius: 8px;
    padding: 20px; text-align: center; margin: 16px 0; font-size: 10pt;
  }
  .arch-diagram .box {
    display: inline-block; border: 2px solid #1565c0; border-radius: 6px;
    padding: 8px 16px; margin: 4px; background: white;
  }
  .arch-diagram .arrow { color: #1565c0; font-size: 16pt; margin: 0 6px; }
  .arch-diagram .label { font-size: 9pt; color: #666; margin: 2px 0; }

  .page-break { page-break-before: always; }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 3px;
    font-size: 9pt; font-weight: bold; margin: 0 3px;
  }
  .badge-green { background: #c8e6c9; color: #2e7d32; }
  .badge-blue { background: #bbdefb; color: #1565c0; }
  .badge-orange { background: #ffe0b2; color: #e65100; }
  .badge-red { background: #ffcdd2; color: #c62828; }
  img { max-width: 100%; }
</style>
</head>
<body>

<!-- ==================== 封面 ==================== -->
<div class="cover">
  <h1>📡 雷达数据存储系统</h1>
  <div class="line"></div>
  <div class="subtitle">部署运维手册 V1.0</div>
  <div class="meta">
    <p>4节点MinIO分布式集群 + 双Nginx负载均衡</p>
    <p>Keepalived VIP高可用 + 分层存储 + 自动生命周期管理</p>
    <p>支持 20 ~ 50 部雷达平滑扩展</p>
    <br><br><br>
    <p>文档版本：1.0</p>
    <p>更新日期：2026年6月19日</p>
  </div>
</div>

<!-- ==================== 目录 ==================== -->
<div class="toc">
  <h2>目 录</h2>
  <ul>
    <li><a href="#s1">1. 系统概述</a></li>
    <li class="l2"><a href="#s1-1">1.1 架构设计</a></li>
    <li class="l2"><a href="#s1-2">1.2 核心特性</a></li>
    <li class="l2"><a href="#s1-3">1.3 数据流向</a></li>
    <li><a href="#s2">2. 环境要求</a></li>
    <li class="l2"><a href="#s2-1">2.1 硬件要求</a></li>
    <li class="l2"><a href="#s2-2">2.2 软件要求</a></li>
    <li class="l2"><a href="#s2-3">2.3 网络规划</a></li>
    <li><a href="#s3">3. 快速部署</a></li>
    <li class="l2"><a href="#s3-1">3.1 目录结构</a></li>
    <li class="l2"><a href="#s3-2">3.2 部署步骤</a></li>
    <li class="l2"><a href="#s3-3">3.3 访问入口</a></li>
    <li><a href="#s4">4. 组件详解</a></li>
    <li class="l2"><a href="#s4-1">4.1 MinIO分布式集群</a></li>
    <li class="l2"><a href="#s4-2">4.2 Nginx负载均衡</a></li>
    <li class="l2"><a href="#s4-3">4.3 Keepalived VIP</a></li>
    <li class="l2"><a href="#s4-4">4.4 分层存储</a></li>
    <li class="l2"><a href="#s4-5">4.5 生命周期管理</a></li>
    <li class="l2"><a href="#s4-6">4.6 雷达模拟器</a></li>
    <li class="l2"><a href="#s4-7">4.7 监控面板</a></li>
    <li><a href="#s5">5. 运维管理</a></li>
    <li class="l2"><a href="#s5-1">5.1 管理命令</a></li>
    <li class="l2"><a href="#s5-2">5.2 水平扩展</a></li>
    <li class="l2"><a href="#s5-3">5.3 日常监控</a></li>
    <li class="l2"><a href="#s5-4">5.4 日志查看</a></li>
    <li class="l2"><a href="#s5-5">5.5 数据备份</a></li>
    <li><a href="#s6">6. 故障排除</a></li>
    <li class="l2"><a href="#s6-1">6.1 容器启动失败</a></li>
    <li class="l2"><a href="#s6-2">6.2 MinIO集群离线</a></li>
    <li class="l2"><a href="#s6-3">6.3 VIP漂移不生效</a></li>
    <li class="l2"><a href="#s6-4">6.4 分层存储异常</a></li>
    <li class="l2"><a href="#s6-5">6.5 Nginx配置验证</a></li>
    <li><a href="#s7">7. 安全建议</a></li>
    <li><a href="#s8">8. 附录</a></li>
    <li class="l2"><a href="#s8-1">8.1 配置文件索引</a></li>
    <li class="l2"><a href="#s8-2">8.2 常用命令速查</a></li>
  </ul>
</div>

<!-- ==================== 1. 系统概述 ==================== -->
<h1 id="s1">1. 系统概述</h1>

<p>本系统是一套面向雷达数据存储场景的高可用分布式存储解决方案，基于 <strong>4节点MinIO集群</strong> 提供对象存储服务，通过 <strong>双Nginx负载均衡 + Keepalived VIP漂移</strong> 实现高可用接入，并配备 <strong>分层存储</strong> 和 <strong>自动生命周期管理</strong> 能力。</p>

<h2 id="s1-1">1.1 架构设计</h2>

<div class="arch-diagram">
  <div style="display:flex; align-items:center; justify-content:center; flex-wrap:wrap;">
    <div>
      <div class="box">📡 雷达设备<br><span style="font-size:8pt;color:#999;">20 ~ 50 部</span></div>
    </div>
    <div class="arrow">→</div>
    <div>
      <div class="box" style="border-color:#f57c00;">🌐 Nginx-LB1<br><span style="font-size:8pt;">172.20.0.31:18080</span></div>
      <div style="font-size:8pt;color:#999;">主负载均衡</div>
    </div>
    <div class="arrow" style="display:block;margin:2px 0;">↑ ↓</div>
    <div style="font-size:9pt;color:#1565c0;font-weight:bold;">VIP 172.20.0.100<br><span style="font-size:8pt;color:#999;">Keepalived 管理</span></div>
    <div class="arrow" style="display:block;margin:2px 0;">↓ ↑</div>
    <div>
      <div class="box" style="border-color:#f57c00;">🌐 Nginx-LB2<br><span style="font-size:8pt;">172.20.0.32:18080</span></div>
      <div style="font-size:8pt;color:#999;">备负载均衡</div>
    </div>
    <div class="arrow" style="width:100%;margin:8px 0;">↓ 负载均衡分發</div>
    <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:center;">
      <div class="box" style="border-color:#2e7d32;">📦 MinIO-1<br><span style="font-size:8pt;">172.20.0.11</span></div>
      <div class="box" style="border-color:#2e7d32;">📦 MinIO-2<br><span style="font-size:8pt;">172.20.0.12</span></div>
      <div class="box" style="border-color:#2e7d32;">📦 MinIO-3<br><span style="font-size:8pt;">172.20.0.13</span></div>
      <div class="box" style="border-color:#2e7d32;">📦 MinIO-4<br><span style="font-size:8pt;">172.20.0.14</span></div>
    </div>
    <div style="font-size:9pt;color:#2e7d32;margin:4px 0;">4 节点分布式集群（热存储层）</div>
    <div class="arrow">↓ ILM 生命周期 →</div>
    <div>
      <div class="box" style="border-color:#6a1b9a;">❄️ MinIO-Cold<br><span style="font-size:8pt;">172.20.0.20</span></div>
      <div style="font-size:8pt;color:#999;">冷存储层（归档）</div>
    </div>
  </div>
</div>

<h2 id="s1-2">1.2 核心特性</h2>

<table>
  <tr><th style="width:160px;">特性</th><th>说明</th></tr>
  <tr><td>高可用</td><td>4节点MinIO分布式集群 + 双Nginx负载均衡 + Keepalived VIP漂移</td></tr>
  <tr><td>自动分层</td><td>热数据保留在本地集群，冷数据自动过渡到归档存储</td></tr>
  <tr><td>生命周期管理</td><td>基于时间的自动过期删除、存储类转换，无需人工干预</td></tr>
  <tr><td>弹性扩展</td><td>支持 20~50 部雷达，增加存储节点即可线性扩展容量和性能</td></tr>
  <tr><td>数据安全</td><td>MinIO Erasure Coding 数据保护、桶版本控制、对象锁定</td></tr>
  <tr><td>实时监控</td><td>Web 监控面板，实时查看集群状态、存储使用量和数据吞吐</td></tr>
</table>

<h2 id="s1-3">1.3 数据流向</h2>

<ol>
  <li><strong>写入路径</strong>：雷达模拟器 → Nginx负载均衡器（S3 API） → MinIO集群节点 → 分布式存储</li>
  <li><strong>读取路径</strong>：客户端 → VIP地址 → Nginx主节点（故障时自动切换备节点）→ MinIO集群</li>
  <li><strong>生命周期</strong>：实时数据写入 rada-data 桶 → 7天后过渡到冷存储COLD-TIER-S3 → 90天后过期清理</li>
  <li><strong>高可用切换</strong>：Keepalived 每5秒检测MinIO集群健康，主节点故障时VIP自动漂移至备节点</li>
</ol>

<!-- ==================== 2. 环境要求 ==================== -->
<div class="page-break"></div>
<h1 id="s2">2. 环境要求</h1>

<h2 id="s2-1">2.1 硬件要求</h2>

<table>
  <tr><th>部署规模</th><th>雷达数</th><th>CPU</th><th>内存</th><th>磁盘</th></tr>
  <tr><td>测试环境</td><td>20部</td><td>4核</td><td>8 GB</td><td>50 GB</td></tr>
  <tr><td>小型生产</td><td>20~30部</td><td>8核</td><td>32 GB</td><td>500 GB SSD</td></tr>
  <tr><td>中型生产</td><td>30~50部</td><td>16核</td><td>64 GB</td><td>1 TB NVMe</td></tr>
</table>

<h2 id="s2-2">2.2 软件要求</h2>

<table>
  <tr><th>组件</th><th>版本要求</th><th>说明</th></tr>
  <tr><td>Docker</td><td>≥ 24.x</td><td>容器运行环境</td></tr>
  <tr><td>Docker Compose</td><td>≥ 2.20</td><td>容器编排工具</td></tr>
  <tr><td>MinIO</td><td>RELEASE.2024-01-11T07-46-16Z</td><td>对象存储服务</td></tr>
  <tr><td>Nginx</td><td>1.25-alpine</td><td>负载均衡器</td></tr>
  <tr><td>Keepalived</td><td>latest (Alpine)</td><td>VIP漂移管理</td></tr>
  <tr><td>Python</td><td>3.11+</td><td>模拟器和监控脚本运行环境</td></tr>
</table>

<div class="tip">
  <strong>提示：</strong>生产环境建议提前拉取镜像避免部署时等待：
  <pre><code>docker pull minio/minio:RELEASE.2024-01-11T07-46-16Z
docker pull nginx:1.25-alpine
docker pull minio/mc:latest
docker pull python:3.11-alpine
docker pull alpine:3.18</code></pre>
</div>

<h2 id="s2-3">2.3 网络规划</h2>

<table>
  <tr><th>组件</th><th>内部IP</th><th>外部端口</th><th>协议</th></tr>
  <tr><td>MinIO Node1</td><td>172.20.0.11</td><td>9011 (S3) / 19111 (Console)</td><td>HTTP</td></tr>
  <tr><td>MinIO Node2</td><td>172.20.0.12</td><td>9012 (S3) / 19112 (Console)</td><td>HTTP</td></tr>
  <tr><td>MinIO Node3</td><td>172.20.0.13</td><td>9013 (S3) / 19113 (Console)</td><td>HTTP</td></tr>
  <tr><td>MinIO Node4</td><td>172.20.0.14</td><td>9014 (S3) / 19114 (Console)</td><td>HTTP</td></tr>
  <tr><td>MinIO Cold</td><td>172.20.0.20</td><td>9020 (S3) / 19220 (Console)</td><td>HTTP</td></tr>
  <tr><td>Nginx LB1</td><td>172.20.0.31</td><td>18080 (S3) / 18081 (Console) / 19090 (Status)</td><td>HTTP</td></tr>
  <tr><td>Nginx LB2</td><td>172.20.0.32</td><td>28080 (S3) / 28081 (Console) / 29090 (Status)</td><td>HTTP</td></tr>
  <tr><td>Keepalived Master</td><td>172.20.0.41</td><td>-</td><td>VRRP</td></tr>
  <tr><td>Keepalived Backup</td><td>172.20.0.42</td><td>-</td><td>VRRP</td></tr>
  <tr><td><strong>VIP（虚拟IP）</strong></td><td><strong>172.20.0.100</strong></td><td><strong>18080 / 18081</strong></td><td><strong>HTTP</strong></td></tr>
  <tr><td>监控面板</td><td>172.20.0.70</td><td>8888</td><td>HTTP</td></tr>
</table>

<div class="note">
  <strong>注意：</strong>内部IP由Docker桥接网络自动分配，上述为固定分配值。VIP <code>172.20.0.100</code> 由Keepalived管理，默认绑定在主Nginx节点上，主节点故障时自动漂移到备节点。
</div>

<!-- ==================== 3. 快速部署 ==================== -->
<div class="page-break"></div>
<h1 id="s3">3. 快速部署</h1>

<h2 id="s3-1">3.1 目录结构</h2>

<pre><code>radar-storage/
├── docker-compose.yml              # 主编排文件（所有服务定义）
├── manage.sh                       # 统一管理脚本
├── minio/
│   ├── node1~4/                    # 4个分布式节点数据/配置目录
│   └── cold-tier/                  # 冷存储层数据/配置目录
├── nginx/
│   ├── nginx1/                     # 主负载均衡器配置
│   │   ├── nginx.conf
│   │   └── conf.d/
│   │       ├── minio-s3.conf       # S3 API代理配置
│   │       └── status.conf         # 状态监控页面
│   └── nginx2/                     # 备负载均衡器配置（结构同上）
├── keepalived/
│   ├── keepalived-master.conf       # 主节点VIP配置
│   ├── keepalived-backup.conf       # 备节点VIP配置
│   ├── check_minio.sh              # 健康检查脚本
│   └── notify.sh                   # 状态切换通知脚本
├── ilm/
│   ├── ilm-rule-hot-to-warm.json   # ILM规则：热→冷（7天）
│   ├── ilm-rule-warm-to-cold.json  # ILM规则：温→冷（30天）
│   ├── ilm-rule-backup.json        # ILM规则：备份过期（90天）
│   └── radar-policy.json           # MinIO访问策略
└── scripts/
    ├── init_minio.sh               # MinIO集群初始化脚本
    ├── radar_simulator.py           # 雷达数据模拟器
    ├── monitor_server.py            # 监控面板服务
    └── health_check.py              # 健康检查工具</code></pre>

<h2 id="s3-2">3.2 部署步骤</h2>

<h3>3.2.1 下载项目</h3>
<pre><code>cd /workspace/radar-storage</code></pre>

<h3>3.2.2 一键启动</h3>
<pre><code>./manage.sh start</code></pre>

<p>该命令将依次完成：</p>
<ol>
  <li>自动创建 Docker 网络和持久化数据卷</li>
  <li>拉取所有镜像（第一次启动时）</li>
  <li>启动4个MinIO分布式节点（自动形成集群）</li>
  <li>启动冷存储 MinIO 实例</li>
  <li>启动双 Nginx 负载均衡器</li>
  <li>启动 Keepalived 主备节点（建立VIP）</li>
  <li>执行初始化脚本：创建桶、配置分层存储、设置ILM策略、创建服务账号</li>
  <li>启动雷达模拟器（自动写入数据）</li>
  <li>启动监控面板</li>
</ol>

<h3>3.2.3 验证部署</h3>

<pre><code># 查看所有容器状态
./manage.sh status

# 运行健康检查
./manage.sh health

# 查看MinIO集群信息
docker exec radar-mc-init mc admin info hot</code></pre>

<h2 id="s3-3">3.3 访问入口</h2>

<table>
  <tr><th>服务</th><th>地址</th><th>凭证</th></tr>
  <tr><td>MinIO Console（节点1）</td><td>http://localhost:19111</td><td>radaradmin / RadarAdmin@2024!</td></tr>
  <tr><td>MinIO Console（节点2）</td><td>http://localhost:19112</td><td>同上</td></tr>
  <tr><td>S3 API（主负载均衡）</td><td>http://localhost:18080</td><td>-</td></tr>
  <tr><td>S3 API（备负载均衡）</td><td>http://localhost:28080</td><td>-</td></tr>
  <tr><td>Nginx状态页（主）</td><td>http://localhost:19090/status</td><td>-</td></tr>
  <tr><td>监控面板</td><td>http://localhost:8888</td><td>-</td></tr>
  <tr><td>VIP入口</td><td>http://172.20.0.100:18080</td><td>-</td></tr>
</table>

<div class="tip">
  <strong>提示：</strong>雷达模拟器使用服务账号 <code>radar-simulator / RadarSim@2024!</code> 通过Nginx负载均衡写入数据，测试客户端连接时也应使用此地址。
</div>

<!-- ==================== 4. 组件详解 ==================== -->
<div class="page-break"></div>
<h1 id="s4">4. 组件详解</h1>

<h2 id="s4-1">4.1 MinIO分布式集群</h2>

<h3>节点配置</h3>
<p>4个MinIO节点通过 <code>http://minio-node{1...4}/data</code> 组成分布式集群。所有节点必须具有完全一致的环境变量，否则集群启动会报错。</p>

<pre><code># 关键环境变量
MINIO_ROOT_USER=radaradmin
MINIO_ROOT_PASSWORD=RadarAdmin@2024!
MINIO_SITE_REGION=cn-east-1
MINIO_PROMETHEUS_AUTH_TYPE=public</code></pre>

<h3>启动命令</h3>
<pre><code>server --console-address ":9001" http://minio-node{1...4}/data</code></pre>

<p>使用 <code>{1...4}</code> 通配符语法自动识别集群成员。</p>

<h3>健康检查</h3>
<p>Docker healthcheck 使用 bash 内置TCP连接测试：</p>
<pre><code>bash -c "exec 3<>/dev/tcp/localhost/9000"</code></pre>

<h3>存储桶规划</h3>
<table>
  <tr><th>桶名</th><th>用途</th><th>标签</th><th>配额</th></tr>
  <tr><td>radar-data</td><td>实时雷达数据</td><td>radar-type=real-time, retention=hot</td><td>100 GB</td></tr>
  <tr><td>radar-archive</td><td>归档数据</td><td>radar-type=archive, retention=warm</td><td>200 GB</td></tr>
  <tr><td>radar-backup</td><td>备份数据</td><td>radar-type=backup, retention=warm</td><td>无限制</td></tr>
</table>

<h2 id="s4-2">4.2 Nginx负载均衡</h2>

<table>
  <tr><th>配置项</th><th>值</th><th>说明</th></tr>
  <tr><td>负载均衡算法</td><td>least_conn</td><td>最少连接数，适合大文件传输场景</td></tr>
  <tr><td>连接保持</td><td>keepalive 32</td><td>复用后端连接，减少TCP开销</td></tr>
  <tr><td>超时设置</td><td>connect 30s / send 300s / read 300s</td><td>适应雷达大文件传输</td></tr>
  <tr><td>失败重试</td><td>max_fails=3, fail_timeout=30s</td><td>节点故障自动摘除</td></tr>
  <tr><td>缓冲区</td><td>proxy_buffering off</td><td>禁用缓冲，适配流式传输</td></tr>
  <tr><td>最大请求体</td><td>client_max_body_size 0</td><td>无限制，支持超大文件</td></tr>
</table>

<p><strong>主备Nginx差异：</strong>两个节点的Nginx配置基本相同，区别在于响应头 <code>X-Node</code> 分别标识 <code>nginx-lb1</code> 和 <code>nginx-lb2</code>，便于排查请求走了哪个节点。</p>

<h2 id="s4-3">4.3 Keepalived VIP漂移</h2>

<table>
  <tr><th>配置项</th><th>主节点</th><th>备节点</th></tr>
  <tr><td>优先级</td><td>150</td><td>100</td></tr>
  <tr><td>VRRP ID</td><td>51</td><td>51</td></tr>
  <tr><td>通告间隔</td><td>1秒</td><td>1秒</td></tr>
  <tr><td>抢占模式</td><td>开启（延迟10秒）</td><td>关闭（nopreempt）</td></tr>
  <tr><td>健康检查脚本</td><td>check_minio.sh（5秒间隔）</td><td>同左</td></tr>
</table>

<p><strong>切换条件：</strong>MinIO集群超过半数节点宕机 → 健康检查失败 → 优先级降低 → VIP漂移到备节点。</p>

<div class="note">
  <strong>注意：</strong>在Docker中运行Keepalived需要 <code>privileged: true</code> 和 <code>NET_ADMIN, NET_RAW, NET_BROADCAST</code> 权限。
</div>

<h2 id="s4-4">4.4 分层存储</h2>

<p>系统配置了 <strong>COLD-TIER-S3</strong> 远程存储层，将MinIO冷存储实例作为归档目标：</p>

<pre><code>mc admin tier add minio hot COLD-TIER-S3 \\
    --endpoint http://minio-cold:9000 \\
    --access-key radaradmin \\
    --secret-key 'RadarAdmin@2024!' \\
    --bucket radar-archive-cold \\
    --region cn-east-1</code></pre>

<div class="arch-diagram">
  <strong>存储分层结构</strong><br><br>
  <span class="badge badge-green">热层</span> 4节点MinIO集群（本地SSD）<br>
  <span class="arrow" style="font-size:12pt;">↓ ILM 7/30天后自动转移</span><br>
  <span class="badge badge-blue">冷层</span> COLD-TIER-S3（远程归档存储）
</div>

<h2 id="s4-5">4.5 生命周期管理</h2>

<p>系统配置了3条ILM规则，实现数据全生命周期自动管理：</p>

<table>
  <tr><th>桶</th><th>规则</th><th>触发条件</th><th>动作</th></tr>
  <tr><td>radar-data</td><td>hot-to-warm-7d</td><td>非当前版本 7天</td><td>过渡到 COLD-TIER-S3</td></tr>
  <tr><td>radar-data</td><td>hot-to-warm-7d</td><td>当前版本 90天</td><td>过期删除</td></tr>
  <tr><td>radar-archive</td><td>warm-to-cold-30d</td><td>非当前版本 30天</td><td>过渡到 COLD-TIER-S3</td></tr>
  <tr><td>radar-archive</td><td>warm-to-cold-30d</td><td>当前版本 365天</td><td>过期删除</td></tr>
  <tr><td>radar-backup</td><td>backup-expire-90d</td><td>当前版本 90天</td><td>过期删除</td></tr>
  <tr><td>radar-backup</td><td>backup-expire-90d</td><td>非当前版本 30天</td><td>过期删除</td></tr>
</table>

<h2 id="s4-6">4.6 雷达模拟器</h2>

<p>模拟器支持4种雷达类型，按加权概率随机分配：</p>

<table>
  <tr><th>雷达类型</th><th>数据量</th><th>上报间隔</th><th>S3前缀</th><th>优先级</th></tr>
  <tr><td>气象雷达 weather</td><td>1~5 MB</td><td>5分钟</td><td>weather/</td><td>高</td></tr>
  <tr><td>监视雷达 surveillance</td><td>5~20 MB</td><td>1分钟</td><td>surveillance/</td><td>关键</td></tr>
  <tr><td>成像雷达 imaging</td><td>10~50 MB</td><td>10分钟</td><td>imaging/</td><td>中</td></tr>
  <tr><td>跟踪雷达 tracking</td><td>0.5~2 MB</td><td>10秒</td><td>tracking/</td><td>关键</td></tr>
</table>

<p>数据存储路径格式：<code>{prefix}/{radar-id}/YYYY/MM/DD/HH/MM/{radar-id}_timestamp_uuid.radar</code></p>

<h2 id="s4-7">4.7 监控面板</h2>

<p>Flask Web监控服务，提供：</p>
<ul>
  <li>集群概览：桶数量、对象总数、总数据量</li>
  <li>存储桶详情：每个桶的对象数、数据量、标签</li>
  <li>最近上传活动日志</li>
  <li>JSON API端点供外部监控系统集成</li>
</ul>

<div class="tip">
  <strong>集成建议：</strong>监控面板提供 <code>/api/status</code> 和 <code>/api/buckets</code> API，可对接 Prometheus + Grafana 或 Zabbix 等企业监控平台。
</div>

<!-- ==================== 5. 运维管理 ==================== -->
<div class="page-break"></div>
<h1 id="s5">5. 运维管理</h1>

<h2 id="s5-1">5.1 管理命令</h2>

<pre><code># 系统管理
./manage.sh start          # 启动系统
./manage.sh stop           # 停止系统
./manage.sh restart        # 重启系统
./manage.sh status         # 查看容器状态
./manage.sh health         # 健康检查

# 扩展运维
./manage.sh scale 35       # 调整雷达数量（1-50）
./manage.sh logs minio-node1  # 查看指定服务日志
./manage.sh clean          # 清理所有数据卷（慎用！）
</code></pre>

<h2 id="s5-2">5.2 水平扩展</h2>

<h3>扩展MinIO节点</h3>
<p>从4节点扩展到更多节点（如6节点），只需在 docker-compose.yml 中新增节点定义，启动命令改为：</p>
<pre><code>server --console-address ":9001" http://minio-node{1...N}/data</code></pre>

<h3>扩展雷达数量</h3>
<pre><code># 调整雷达模拟器数量
./manage.sh scale 50       # 立即扩展到50部雷达</code></pre>

<h2 id="s5-3">5.3 日常监控</h2>

<pre><code># 实时资源监控
docker stats $(docker compose ps -q)

# MinIO集群状态
docker exec radar-mc-init mc admin info hot
docker exec radar-mc-init mc admin disk hot

# MinIO集群性能
docker exec radar-mc-init mc admin perf hot

# 查看存储桶使用量
docker exec radar-mc-init mc du hot --recursive

# 查看ILM策略
docker exec radar-mc-init mc ilm ls hot/radar-data</code></pre>

<h2 id="s5-4">5.4 日志查看</h2>

<pre><code># 查看所有日志（实时）
docker compose logs -f

# 查看特定服务日志
docker compose logs -f minio-node1
docker compose logs -f radar-simulator
docker compose logs -f nginx-lb1

# 仅查看最近50行
docker compose logs --tail=50 minio-node1</code></pre>

<h2 id="s5-5">5.5 数据备份</h2>

<pre><code># MinIO桶备份到冷存储（手动触发）
docker exec radar-mc-init mc mirror hot/radar-data cold/radar-archive-cold

# 使用mc创建桶快照
docker exec radar-mc-init mc cp --recursive hot/radar-data cold/radar-backup/$(date +%Y%m%d)

# 导出MinIO配置
docker exec radar-mc-init mc admin config get hot</code></pre>

<!-- ==================== 6. 故障排除 ==================== -->
<div class="page-break"></div>
<h1 id="s6">6. 故障排除</h1>

<h2 id="s6-1">6.1 容器启动失败</h2>

<table>
  <tr><th>现象</th><th>原因</th><th>解决方案</th></tr>
  <tr><td>MinIO节点 unhealthy</td><td>镜像版本不对或环境变量不一致</td><td>确保所有节点有相同的 <code>MINIO_ROOT_USER</code> 等环境变量</td></tr>
  <tr><td>keepalived 反复重启</td><td>脚本挂载为只读，chmod失败</td><td>挂载脚本卷时去掉 <code>:ro</code> 标记</td></tr>
  <tr><td>端口冲突</td><td>外部端口已被占用</td><td>修改 docker-compose.yml 中的端口映射</td></tr>
</table>

<h3>修复步骤</h3>
<pre><code># 1. 查看容器日志定位问题
docker logs radar-minio-node1

# 2. 清理并重启
./manage.sh clean && ./manage.sh start

# 3. 或单独重建特定容器
docker compose up -d --force-recreate minio-node1</code></pre>

<h2 id="s6-2">6.2 MinIO集群离线</h2>

<table>
  <tr><th>检查命令</th><th>预期输出</th><th>异常处理</th></tr>
  <tr><td><code>mc admin info hot</code></td><td>4 Online</td><td>检查网络连通性：<code>ping minio-node2</code></td></tr>
  <tr><td><code>docker ps | grep minio</code></td><td>4个节点healthy</td><td>重启故障节点：<code>docker restart radar-minio-nodeX</code></td></tr>
  <tr><td><code>curl localhost:9011/minio/health/live</code></td><td>HTTP 200</td><td>检查磁盘空间：<code>df -h</code></td></tr>
</table>

<h2 id="s6-3">6.3 VIP漂移不生效</h2>

<pre><code># 检查Keepalived进程
docker exec radar-keepalived-master ps aux | grep keepalived

# 检查VIP是否绑定
docker exec radar-keepalived-master ip addr show eth0

# 查看Keepalived日志
docker logs radar-keepalived-master

# 手动测试健康检查脚本
docker exec radar-keepalived-master sh /usr/local/bin/check_minio.sh</code></pre>

<h2 id="s6-4">6.4 分层存储异常</h2>

<pre><code># 查看已配置的存储层
docker exec radar-mc-init mc admin tier ls hot

# 检查分区状态
docker exec radar-mc-init mc ilm ls hot/radar-data

# 手动触发ILM扫描（MinIO每小时自动扫描）
docker exec radar-mc-init mc ilm ls hot/radar-data --verbose</code></pre>

<h2 id="s6-5">6.5 Nginx配置验证</h2>

<pre><code># 检查Nginx配置语法
docker exec radar-nginx-lb1 nginx -t

# 查看Nginx访问日志
docker exec radar-nginx-lb1 cat /var/log/nginx/minio-s3-access.log

# 查看Nginx错误日志
docker exec radar-nginx-lb1 cat /var/log/nginx/error.log</code></pre>

<!-- ==================== 7. 安全建议 ==================== -->
<div class="page-break"></div>
<h1 id="s7">7. 安全建议</h1>

<table>
  <tr><th>#</th><th>建议</th><th>说明</th></tr>
  <tr><td>1</td><td>修改默认密码</td><td>部署后立即修改 <code>radaradmin</code> 的密码，生产环境使用强密码策略</td></tr>
  <tr><td>2</td><td>启用TLS</td><td>为MinIO和Nginx配置SSL证书，使用HTTPS协议传输雷达数据</td></tr>
  <tr><td>3</td><td>网络隔离</td><td>生产环境将MinIO集群部署在私有网络，仅暴露Nginx负载均衡端口</td></tr>
  <tr><td>4</td><td>访问控制</td><td>为不同雷达设备创建独立服务账号，遵循最小权限原则</td></tr>
  <tr><td>5</td><td>审计日志</td><td>启用MinIO审计日志 (<code>MINIO_AUDIT_WEBHOOK</code>)，记录所有数据访问行为</td></tr>
  <tr><td>6</td><td>版本管理</td><td>对关键桶启用版本控制 (<code>mc version enable</code>)，防止数据误删</td></tr>
  <tr><td>7</td><td>定期巡检</td><td>每周执行 <code>./manage.sh health</code> 检查系统健康，每月检查磁盘容量趋势</td></tr>
  <tr><td>8</td><td>数据加密</td><td>启用MinIO服务端加密 (<code>MINIO_KMS</code>)，确保存储数据加密</td></tr>
</table>

<!-- ==================== 8. 附录 ==================== -->
<div class="page-break"></div>
<h1 id="s8">8. 附录</h1>

<h2 id="s8-1">8.1 配置文件索引</h2>

<table>
  <tr><th>文件</th><th>用途</th><th>关键配置项</th></tr>
  <tr><td>docker-compose.yml</td><td>服务编排定义</td><td>12个服务定义、网络、数据卷</td></tr>
  <tr><td>nginx/nginx1/nginx.conf</td><td>Nginx主配置</td><td>worker_connections, upstream定义</td></tr>
  <tr><td>nginx/nginx1/conf.d/minio-s3.conf</td><td>S3 API代理规则</td><td>端口18080, least_conn, 超时设置</td></tr>
  <tr><td>keepalived/keepalived-master.conf</td><td>VIP主节点</td><td>priority 150, VRRP ID 51</td></tr>
  <tr><td>keepalived/check_minio.sh</td><td>健康检查</td><td>检测4个节点, 满足多数在线即正常</td></tr>
  <tr><td>ilm/ilm-rule-hot-to-warm.json</td><td>热→冷过渡(7天)</td><td>StorageClass: COLD-TIER-S3</td></tr>
  <tr><td>scripts/radar_simulator.py</td><td>雷达数据模拟</td><td>4种雷达类型, 自动分片上传</td></tr>
  <tr><td>scripts/monitor_server.py</td><td>监控Web面板</td><td>Flask, JSON API, 自动刷新</td></tr>
</table>

<h2 id="s8-2">8.2 常用命令速查</h2>

<pre><code># ┌────────────────────────────────────────────────────────┐
# │  管 理 类 命 令                                        │
# └────────────────────────────────────────────────────────┘
./manage.sh start            # 启动全部服务
./manage.sh stop             # 停止全部服务
./manage.sh restart          # 重启全部服务
./manage.sh status           # 查看容器状态
./manage.sh health           # 完整健康检查
./manage.sh scale N          # 调整雷达数量
./manage.sh logs [service]   # 查看日志

# ┌────────────────────────────────────────────────────────┐
# │  MinIO 命 令 类                                       │
# └────────────────────────────────────────────────────────┘
docker exec radar-mc-init mc admin info hot     # 集群信息
docker exec radar-mc-init mc admin disk hot     # 磁盘状态
docker exec radar-mc-init mc admin perf hot     # 性能测试
docker exec radar-mc-init mc ls hot/radar-data  # 列出对象
docker exec radar-mc-init mc du hot --recursive # 存储用量
docker exec radar-mc-init mc ilm ls hot/radar-data  # ILM策略

# ┌────────────────────────────────────────────────────────┐
# │  监 控 诊 断 类                                       │
# └────────────────────────────────────────────────────────┘
docker stats $(docker compose ps -q)            # 实时资源监控
curl http://localhost:18080/minio/health/live   # S3健康检查
curl http://localhost:8888/api/status           # API状态查询
curl http://localhost:19090/status              # Nginx状态

# ┌────────────────────────────────────────────────────────┐
# │  故 障 恢 复 类                                       │
# └────────────────────────────────────────────────────────┘
docker compose logs -f minio-node1              # 节点日志
docker compose up -d --force-recreate [svc]     # 强制重建
docker compose down -v && docker compose up -d  # 完全重置
</code></pre>

<div class="tip">
  <strong>快速参考：</strong>所有MinIO命令使用 <code>docker exec radar-mc-init mc &lt;command&gt;</code> 格式执行，mc-init容器保持运行，可作为MinIO管理代理使用。
</div>

<br><br>
<div style="text-align:center; color:#999; font-size:10pt; border-top:1px solid #e0e0e0; padding-top:20px;">
  雷达数据存储系统 部署运维手册 V1.0<br>
  文档生成日期：2026年6月19日
</div>

</body>
</html>
"""

def main():
    output_path = "/workspace/radar-storage/雷达存储系统_部署运维手册.pdf"
    
    print("正在生成PDF部署手册...")
    HTML(string=HTML_CONTENT).write_pdf(output_path)
    
    size = os.path.getsize(output_path)
    print(f"✅ 手册生成完成: {output_path}")
    print(f"   文件大小: {size / 1024:.1f} KB")
    
    return output_path

if __name__ == "__main__":
    main()

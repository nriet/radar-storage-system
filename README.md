
<br>
<div align="center">
  <h1>📡 雷达数据存储系统</h1>
  <p><strong>Radar Data Storage System</strong></p>
  <p>
    4节点 MinIO 分布式集群 · 双 Nginx 负载均衡 · Keepalived VIP 漂移<br>
    分层存储（热/冷）· 自动生命周期管理 · 支持 20~50 部雷达平滑扩展
  </p>
  <br>
  <p>
    <a href="#-架构概览">架构概览</a> •
    <a href="#-快速开始">快速开始</a> •
    <a href="#-组件说明">组件说明</a> •
    <a href="#-运维管理">运维管理</a> •
    <a href="#-故障排除">故障排除</a>
  </p>
  <br>
</div>

---

## 📋 架构概览

```
┌──────────────────────────────────────────────────────────────────┐
│                          📡 雷达设备                             │
│                     （20 ~ 50 部）                               │
└──────────────────────────┬───────────────────────────────────────┘
                           │ S3 API
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  🌐 双 Nginx 负载均衡 + Keepalived VIP 漂移                      │
│  ┌────────────────────┐         ┌────────────────────┐          │
│  │   nginx-lb1 (主)   │◄── VIP ─►│   nginx-lb2 (备)   │          │
│  │   172.20.0.31      │  172.20.0.100 │   172.20.0.32      │          │
│  └────────┬───────────┘         └────────┬───────────┘          │
└───────────┼──────────────────────────────┼───────────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  📦 4 节点 MinIO 分布式集群（热存储层）                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                    │
│  │Node 1  │ │Node 2  │ │Node 3  │ │Node 4  │                    │
│  │:9001   │ │:9002   │ │:9003   │ │:9004   │                    │
│  └────────┘ └────────┘ └────────┘ └────────┘                    │
│   Erasure Coding 纠删码保护                                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │ ILM 生命周期：7天/30天自动过渡
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  ❄️ MinIO 冷存储层（归档）                                        │
│  cold-tier-s3 /radar-archive-cold                                │
└──────────────────────────────────────────────────────────────────┘
```

### 核心特性

| 特性 | 说明 |
|------|------|
| **高可用** | 4节点分布式 + 双Nginx + Keepalived VIP 自动漂移 |
| **自动分层** | 热数据 7天 → 冷存储，归档数据 30天 → 冷存储 |
| **生命周期管理** | 自动过期删除，无需人工干预 |
| **弹性扩展** | 20~50部雷达线性扩展，增加 MinIO 节点即可扩容 |
| **数据保护** | MinIO Erasure Coding、桶版本控制、对象锁定 |
| **实时监控** | Web 面板实时查看集群状态和数据吞吐 |

---

## 🚀 快速开始

### 环境要求

- Docker ≥ 24.x
- Docker Compose ≥ 2.20

### 一键部署

```bash
# 克隆项目
git clone https://github.com/nriet/radar-storage-system.git
cd radar-storage-system

# 一键部署（自动完成所有步骤）
./deploy.sh
```

部署脚本会自动完成：
1. ✅ 环境检查 —— Docker、端口、磁盘空间
2. ✅ 拉取镜像 —— MinIO、Nginx、Keepalived 等
3. ✅ 配置验证 —— 检查所有配置文件完整性
4. ✅ 启动服务 —— 拉起 12 个容器
5. ✅ 等待就绪 —— 等待 MinIO 集群健康
6. ✅ 验证部署 —— 检查所有端点可用

### 访问入口

| 服务 | 地址 | 凭证 |
|------|------|------|
| MinIO Console | http://localhost:19111 ~ 19114 | `radaradmin` / `RadarAdmin@2024!` |
| S3 API（主） | http://localhost:18080 | — |
| S3 API（备） | http://localhost:28080 | — |
| Nginx 状态（主） | http://localhost:19090/status | — |
| Nginx 状态（备） | http://localhost:29090/status | — |
| 监控面板 | http://localhost:8888 | — |
| VIP 入口 | http://172.20.0.100:18080 | — |

---

## 🧩 组件说明

### MinIO 分布式集群

4 个节点通过 `http://minio-node{1...4}/data` 组成分布式集群。

```yaml
# 关键环境变量（所有节点必须一致）
MINIO_ROOT_USER=radaradmin
MINIO_ROOT_PASSWORD=RadarAdmin@2024!
MINIO_SITE_REGION=cn-east-1
```

**存储桶规划：**

| 桶名 | 用途 | ILM 策略 |
|------|------|----------|
| `radar-data` | 实时雷达数据 | 7天→冷存储，90天过期 |
| `radar-archive` | 归档数据 | 30天→冷存储，365天过期 |
| `radar-backup` | 备份数据 | 90天过期 |

### Nginx 负载均衡

- **算法**：`least_conn`（最少连接，适合大文件传输）
- **连接保持**：`keepalive 32`
- **超时**：connect 30s / send 300s / read 300s
- **健康检查**：自动摘除故障节点，30秒后恢复重试

### Keepalived VIP 漂移

| 配置 | 主节点 | 备节点 |
|------|--------|--------|
| 优先级 | 150 | 100 |
| 检查间隔 | 5 秒 | 5 秒 |
| 切换条件 | MinIO 半数节点宕机 | 自动接管 VIP |

### 分层存储

```
热层（hot） ──ILM──▶  冷层（cold）
 4节点MinIO          COLD-TIER-S3
（本地SSD）          （远程归档）
```

### 生命周期管理（ILM）

| 桶 | 规则 | 动作 |
|----|------|------|
| radar-data | 非当前版本 ≥ 7天 | 过渡到 COLD-TIER-S3 |
| radar-data | 当前版本 ≥ 90天 | 过期删除 |
| radar-archive | 非当前版本 ≥ 30天 | 过渡到 COLD-TIER-S3 |
| radar-archive | 当前版本 ≥ 365天 | 过期删除 |
| radar-backup | 当前版本 ≥ 90天 | 过期删除 |

### 雷达模拟器

支持 4 种雷达类型，自动模拟数据写入：

| 类型 | 数据量 | 间隔 | 存储前缀 |
|------|--------|------|----------|
| 🌤️ 气象雷达 | 1~5 MB | 5 分钟 | `weather/` |
| 🛩️ 监视雷达 | 5~20 MB | 1 分钟 | `surveillance/` |
| 🛰️ 成像雷达 | 10~50 MB | 10 分钟 | `imaging/` |
| 🎯 跟踪雷达 | 0.5~2 MB | 10 秒 | `tracking/` |

数据路径格式：`{type}/{radar-id}/YYYY/MM/DD/HH/MM/{radar-id}_timestamp_uuid.radar`

---

## 🔧 运维管理

```bash
# 系统管理
./manage.sh start          # 启动系统
./manage.sh stop           # 停止系统
./manage.sh restart        # 重启系统
./manage.sh status         # 查看容器状态
./manage.sh health         # 健康检查

# 扩展运维
./manage.sh scale 35       # 调整雷达数量（1-50）
./manage.sh logs minio-node1  # 查看容器日志
./manage.sh clean          # 清理所有数据（慎用！）

# MinIO 集群管理
docker exec radar-mc-init mc admin info hot        # 集群信息
docker exec radar-mc-init mc admin disk hot        # 磁盘状态
docker exec radar-mc-init mc admin perf hot        # 性能测试
docker exec radar-mc-init mc du hot --recursive    # 存储用量
docker exec radar-mc-init mc ilm ls hot/radar-data # ILM 策略

# 实时监控
docker stats $(docker compose ps -q)               # 容器资源
curl http://localhost:8888/api/status              # 系统状态 API
```

---

## 🐛 故障排除

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| MinIO 节点 unhealthy | 环境变量不一致 | 确保所有节点有相同的 `MINIO_*` 变量 |
| Keepalived 重启 | 脚本权限问题 | 挂载脚本时去掉 `:ro` 标记 |
| 端口冲突 | 端口被占用 | 修改 `docker-compose.yml` 端口映射 |
| VIP 不漂移 | 健康检查失败 | 执行 `docker exec radar-keepalived-master sh /usr/local/bin/check_minio.sh` |
| ILM 无效 | 存储类名称不匹配 | 检查 `mc admin tier ls hot` 输出的名称是否与 ILM JSON 一致 |

---

## 📁 项目结构

```
radar-storage/
├── deploy.sh                    # 一键部署脚本
├── docker-compose.yml           # 12 个服务的编排定义
├── manage.sh                    # 统一管理脚本
├── minio/                       # MinIO 数据目录
│   ├── node{1..4}/              # 4 个分布式节点
│   └── cold-tier/               # 冷存储层
├── nginx/                       # Nginx 负载均衡配置
│   ├── nginx1/                  # 主节点
│   │   ├── nginx.conf
│   │   └── conf.d/minio-s3.conf
│   └── nginx2/                  # 备节点
├── keepalived/                  # VIP 漂移配置
│   ├── keepalived-{master,backup}.conf
│   ├── check_minio.sh           # 健康检查脚本
│   └── notify.sh                # 状态通知脚本
├── ilm/                         # 生命周期管理策略
│   ├── ilm-rule-{hot-to-warm,warm-to-cold,backup}.json
│   └── radar-policy.json        # 访问策略
├── scripts/                     # 工具脚本
│   ├── init_minio.sh            # 集群初始化
│   ├── radar_simulator.py       # 雷达数据模拟器
│   ├── monitor_server.py        # 监控面板
│   └── health_check.py          # 健康检查工具
└── 雷达存储系统_部署运维手册.pdf  # 完整部署手册（21页）
```

---

## 🛡️ 安全建议

1. **修改默认密码** —— 生产环境立即更换 `radaradmin` 密码
2. **启用 TLS** —— 为 Nginx 和 MinIO 配置 SSL 证书
3. **网络隔离** —— 仅暴露 Nginx 负载均衡端口
4. **最小权限** —— 为不同雷达设备创建独立服务账号
5. **版本控制** —— 对关键桶启用对象版本保护
6. **定期巡检** —— 每周执行 `./manage.sh health`，每月检查磁盘容量

---

<div align="center">
  <p>Made with ❤️ for radar data storage</p>
  <p>
    <a href="https://github.com/nriet/radar-storage-system">GitHub</a> •
    <a href="./雷达存储系统_部署运维手册.pdf">部署手册 PDF</a>
  </p>
</div>

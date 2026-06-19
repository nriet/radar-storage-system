# 📡 雷达数据存储系统

> 架构：UIS 3060 G7 超融合 + Polaris OneStor 分布式块存储  
> 服务：MinIO 热存储 (NVMe) → ILM 7天 → MinIO 冷存储 (HDD)  
> 适用：20~50 部雷达

---

## 🏗️ 架构

```
                        ┌─ 雷达设备 (20~50部) ─┐
                                  │ S3 API
                                  ▼
┌─── UIS 3060 G7 ──────────────────────────────────────────┐
│                                                           │
│  ┌─ VM-1 (4核/32G) ──────────────┐  ┌─ VM-2 (4核/16G) ─┐│
│  │  🌐 Nginx    :18080           │  │  ❄️ MinIO-Cold    ││
│  │  🔥 MinIO-Hot   :9010         │  │     :9020         ││
│  │  📈 Monitor     :8888         │  │                   ││
│  │  /data/nvme{1,2}              │  │  /data/hdd{1,2}   ││
│  └──────────┬────────────────────┘  └──────────┬────────┘│
│             │ OneStor 块存储卷                   │         │
├─────────────┼───────────────────────────────────┼─────────┤
│   OneStor   │   NVMe 3.84T×2   │   HDD 20T×2   │         │
│   分布式     │   副本=2          │   副本=2       │         │
│   块存储     └──────────────────┴────────────────┘         │
├───────────────────────────────────────────────────────────┤
│   Polaris ×3: NVMe 3.84T×2 + SSD 7.68T×12 + HDD 20T×10  │
└───────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 方案 A：单虚拟机（开发/测试 🛠️）

含雷达模拟器，一键启动验证系统功能。

```bash
git clone https://github.com/nriet/radar-storage-system.git
cd radar-storage-system

# UIS 创建 1 台 VM：4核/32GB + 挂载 OneStor 卷×4
./manage.sh start
```

| 服务 | 端口 | 说明 |
|------|------|------|
| MinIO 热 | `:9010` | S3 API（热数据） |
| MinIO 冷 | `:9020` | S3 API（冷数据） |
| Nginx | `:18080` | 统一 S3 入口 |
| MinIO Console | `:18081` | 管理界面 |
| 监控面板 | `:8888` | Web 实时监控 |

### 方案 B：双虚拟机（生产环境 🚀）

两机独立运行，真实雷达接入。**不含模拟器**。

```bash
cd radar-storage-system/dual

# ── VM-2 上执行（冷节点，先部署）──
bash deploy.sh vm2

# ── VM-1 上执行（热节点）──
bash deploy.sh vm1

# ── 回到 VM-1，初始化跨机分层 ──
export COLD_NODE_IP=192.168.x.x   # VM-2 IP
bash deploy.sh init
```

| | 方案A（单机） | 方案B（双机） |
|------|:---:|:---:|
| 用途 | 🛠️ 开发/测试 | 🚀 生产 |
| 模拟器 | ✅ | ❌ |
| VM | 1台 (32G) | 2台 (32G+16G) |
| 存入 OneStor | NVMe+HDD 同机 | NVMe/HDD 分机 |
| 部署命令 | `./manage.sh start` | `bash deploy.sh vm1 && vm2 && init` |

---

## ⚙️ OneStor 卷配置

在 UIS Manager 中为 VM 创建块存储卷：

### VM-1 热节点

| 卷名 | 大小 | 存储池 | VM内挂载点 | 副本 |
|------|------|--------|-----------|------|
| vm1-hot-nvme1 | 3.84 TB | NVMe池 | `/data/nvme1` | 2 |
| vm1-hot-nvme2 | 3.84 TB | NVMe池 | `/data/nvme2` | 2 |

### VM-2 冷节点

| 卷名 | 大小 | 存储池 | VM内挂载点 | 副本 |
|------|------|--------|-----------|------|
| vm2-cold-hdd1 | 20 TB | HDD池 | `/data/hdd1` | 2 |
| vm2-cold-hdd2 | 20 TB | HDD池 | `/data/hdd2` | 2 |

### 格式化挂载

```bash
mkfs.xfs /dev/vdb && mkfs.xfs /dev/vdc
mkdir -p /data/nvme1 /data/nvme2
mount /dev/vdb /data/nvme1 && mount /dev/vdc /data/nvme2
echo '/dev/vdb /data/nvme1 xfs defaults 0 0' >> /etc/fstab
echo '/dev/vdc /data/nvme2 xfs defaults 0 0' >> /etc/fstab
```

---

## 🔄 ILM 生命周期策略

| 桶 | 当前版本过渡 | 历史版本过渡 | 当前版本过期 | 历史版本过期 |
|----|------------|------------|------------|------------|
| `radar-data` | 7天 → COLD-TIER | 7天 → COLD-TIER | 90天 | 180天 |
| `radar-archive` | 30天 → COLD-TIER | 30天 → COLD-TIER | 365天 | 365天 |

```
雷达写入 → radar-data(NVMe) → 7天后 → COLD-TIER → radar-archive-cold(HDD)
                                                         ↓
                                                    90天后过期删除
```

---

## 📁 项目结构

```
radar-storage-system/
├── docker-compose.yml       # 方案A：单机一键部署
├── manage.sh                # 方案A：管理脚本
│
├── single/                  # 方案A 完整文件
│   ├── nginx.conf
│   ├── ilm/                 # ILM 策略 JSON
│   └── scripts/             # 初始化 · 模拟器 · 监控 · 健康检查
│
├── dual/                    # 方案B 完整文件
│   ├── deploy.sh            # 双机部署管理
│   ├── vm1-hot/             # VM-1: docker-compose + nginx
│   ├── vm2-cold/            # VM-2: docker-compose
│   ├── ilm/                 # ILM 策略
│   ├── scripts/             # 初始化 · 监控 · 模拟器(备用)
│   └── manual/              # 安装手册 PDF
│
└── README.md
```

---

## 🔧 日常运维

```bash
# ── 单机方案 ──
./manage.sh start|stop|status|logs

# ── 双机方案 ──
cd dual
bash deploy.sh status-vm1|status-vm2        # 查看状态
bash deploy.sh logs-vm1|logs-vm2 [容器名]    # 查看日志

# ── MinIO 管理 ──
docker exec mc-init mc admin tier ls hot    # 分层状态
docker exec mc-init mc ilm rule ls hot/radar-data  # ILM 策略
docker exec mc-init mc du hot --recursive    # 存储用量
```

---

## 🔑 设计要点

| 决策 | 原因 |
|------|------|
| MinIO 单节点（不做 EC） | OneStor 底层已副本/EC，MinIO 只需存取 |
| 热冷物理分离 | NVMe 低延迟 + HDD 低成本大容量 |
| OneStor 副本数=2 | 足够数据安全，比3副本省33%容量 |
| ILM=7天过渡 | 实时雷达数据7天后转冷，释放NVMe空间 |
| `mc ilm rule add` 方式 | JSON import 对 Transitions 支持有缺陷 |

## 🔑 默认凭证

`radaradmin` / `RadarAdmin@2024!`

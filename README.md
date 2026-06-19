# 📡 雷达数据存储系统

> 架构：UIS 超融合虚拟机 + Polaris OneStor 分布式存储  
> 服务：MinIO 热存储 (NVMe) → ILM 7天 → MinIO 冷存储 (HDD)  
> 适用：20~50 部雷达

---

## 🏗️ 架构

```
UIS 3060 G7 (超融合)
│
├── VM-1: 热数据节点
│     ┌─────────────┐    ┌──────────────┐
│     │ MinIO-Hot    │    │ Nginx        │
│     │ /data/nvme1  │    │ 18080/18081  │
│     │ /data/nvme2  │    └──────────────┘
│     └──────┬───────┘
│            │ 存储卷来自 ↓
│
├── VM-2: 冷数据节点
│     ┌─────────────┐
│     │ MinIO-Cold   │
│     │ /data/hdd1   │
│     │ /data/hdd2   │
│     └──────┬───────┘
│            │ 存储卷来自 ↓
│
├── OneStor 分布式存储层 (块存储)
│    NVMe卷: 3.84T × 2    HDD卷: 20T × 2
│    副本数: 2            副本数: 2
│
└── Polaris × 3 (物理存储节点)
     NVMe 3.84T × 2 + SSD 7.68T × 12 + HDD 20T × 10
```

## 🚀 两种部署方案

### 方案 A：单虚拟机（测试验证）

```bash
cd radar-storage-system

# 在 UIS 创建 1 台 VM (4核/16G)，挂载 OneStor 卷
# /data/nvme1, /data/nvme2, /data/hdd1, /data/hdd2

./manage.sh start
```

| 规格 | 说明 |
|------|------|
| 4核 / 32GB | 热冷同机，Docker 一键部署 |
| OneStor卷 × 4 | 2 NVMe + 2 HDD |

### 方案 B：双虚拟机（生产环境）

```bash
cd radar-storage-system/dual

# VM-1 (4核/32G): 热节点 —— 挂载 2× NVMe OneStor 卷
bash deploy.sh vm1

# VM-2 (4核/16G): 冷节点 —— 挂载 2× HDD OneStor 卷
bash deploy.sh vm2

# VM-1: 初始化分层
export COLD_NODE_IP=<VM-2的IP>
bash deploy.sh init
```

---

## ⚙️ UIS OneStor 存储挂载步骤

在 UIS Manager 中为每台 VM 创建并挂载 OneStor 块存储卷：

### VM-1（热节点）

| 卷名 | 大小 | 存储池 | VM挂载点 | 副本数 |
|------|------|--------|----------|--------|
| vm1-hot-nvme1 | 3.84T | NVMe池 | `/data/nvme1` | 2 |
| vm1-hot-nvme2 | 3.84T | NVMe池 | `/data/nvme2` | 2 |

### VM-2（冷节点）

| 卷名 | 大小 | 存储池 | VM挂载点 | 副本数 |
|------|------|--------|----------|--------|
| vm2-cold-hdd1 | 20T | HDD池 | `/data/hdd1` | 2 |
| vm2-cold-hdd2 | 20T | HDD池 | `/data/hdd2` | 2 |

### VM 内格式化挂载

```bash
# 查看 OneStor 挂载的块设备
lsblk

# 格式化（仅首次）
mkfs.xfs /dev/vdb           # NVMe 卷1
mkfs.xfs /dev/vdc           # NVMe 卷2 (VM-1)
mkfs.xfs /dev/vdb           # HDD 卷1  (VM-2)
mkfs.xfs /dev/vdc           # HDD 卷2  (VM-2)

# 挂载
mkdir -p /data/nvme1 /data/nvme2
mount /dev/vdb /data/nvme1
mount /dev/vdc /data/nvme2

# 持久化
echo '/dev/vdb /data/nvme1 xfs defaults 0 0' >> /etc/fstab
echo '/dev/vdc /data/nvme2 xfs defaults 0 0' >> /etc/fstab
```

---

## 🔑 设计要点

| 决策 | 说明 |
|------|------|
| **MinIO 不做 EC** | OneStor 底层已做副本/EC，MinIO 单节点模式即可 |
| **热冷分离** | 热数据 NVMe（低延迟）、冷数据 HDD（大容量） |
| **副本数=2** | OneStor 2副本足够，省容量，3副本浪费 |
| **ILM=7天** | 实时数据7天后自动过渡到冷层 |

---

## 📁 项目结构

```
├── docker-compose.yml       # 方案A：单机一键启动
├── manage.sh                # 方案A：管理脚本
├── single/                  # 方案A：完整文件
│   ├── nginx.conf · ilm/ · scripts/
├── dual/                    # 方案B：双机部署
│   ├── deploy.sh · vm1-hot/ · vm2-cold/ · manual/
└── README.md
```

## 🔑 默认凭证

`radaradmin` / `RadarAdmin@2024!`

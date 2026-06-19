# 📡 雷达数据存储系统

> UIS 3060 G7 超融合 · Polaris OneStor 分布式存储 · MinIO + JuiceFS  
> 热数据 NVMe → ILM 7天 → 冷数据 HDD · 20~50 部雷达

---

## 🏗️ 架构

```
计算节点 (openEuler 24.03 SP3)
├─ 雷达程序 ──POSIX──▶ JuiceFS Client ──S3──┐
└─ Redis 元数据 ◀────────────────────────────┤
                                              ▼
UIS 3060 G7 ┌──────────────────────────────────────────────┐
            │ VM-1 (4核/32G): Nginx + MinIO热 + Redis      │
            │ VM-2 (4核/16G): MinIO冷                       │
            │ OneStor NVMe卷 + HDD卷 (副本=2)               │
            └──────────────────────────────────────────────┘
Polaris ×3  物理存储节点
```

---

## 🚀 快速开始

### 方案 A：单机 Docker（开发/测试 🛠️ 含模拟器）

```bash
git clone https://github.com/nriet/radar-storage-system.git
cd radar-storage-system
./manage.sh start
```

| 服务 | 端口 | 说明 |
|------|------|------|
| MinIO 热 | `:9010` | S3 API |
| MinIO 冷 | `:9020` | 冷归档 |
| Redis | `:6379` | JuiceFS 元数据 |
| Nginx | `:18080` | 统一入口 |
| 监控 | `:8888` | Web 面板 |

### 方案 B：双机生产（无模拟器 🚀）

```bash
cd dual
# VM-2 先部署
bash deploy.sh vm2
# VM-1 部署
bash deploy.sh vm1
# 初始化分层
export COLD_NODE_IP=<VM-2-IP>
bash deploy.sh init
```

| | 方案 A | 方案 B |
|------|:---:|:---:|
| 用途 | 🛠️ 开发 | 🚀 生产 |
| 模拟器 | ✅ | ❌ |
| 容器数 | 7 | VM1:5 + VM2:1 |

---

## 🍊 JuiceFS 透明 POSIX 集成

将 MinIO 挂载为本地目录，雷达程序无需修改代码：

```bash
# 1. 离线安装 JuiceFS（openEuler）
cd juicefs-offline && bash install.sh

# 2. 创建文件系统（元数据→Redis, 数据→MinIO）
juicefs format --storage minio --bucket http://VM-1-IP:9010/radarfs \
  --access-key radaradmin --secret-key RadarAdmin@2024! \
  redis://VM-1-IP:6379/0 radarfs

# 3. 挂载（路径与原 NFS 一致）
juicefs mount -d --writeback --cache-size 500000 \
  redis://VM-1-IP:6379/0 /data/radar/realtime
```

| 特性 | NFS | JuiceFS |
|------|:---:|:---:|
| POSIX 全兼容 | ✅ | ✅ |
| 文件锁 | ✅ | ✅ |
| 本地 NVMe 缓存 | ❌ | ✅ |
| 多节点共享 | ⚠️ | ✅ |
| 后端存 MinIO | ❌ | ✅ |

---

## 🔄 ILM 生命周期

| 桶 | 过渡到冷层 | 过期删除 |
|----|----------|---------|
| `radar-data` | 7 天 | 90 天 |
| `radar-archive` | 30 天 | 365 天 |

---

## ⚙️ 磁盘挂载（单机生产）

| 磁盘 | 大小 | 角色 | 挂载点 | MinIO |
|------|------|------|--------|-------|
| /dev/vdb | 1.0 TB | 热数据 | `/data` | minio-hot |
| /dev/vdc | 5.0 TB | 冷数据 | `/data_archive` | minio-cold |

单机部署前修改 `docker-compose.yml`：

```yaml
minio-hot:
  volumes:
    - /data:/data          # 替换 hot-data

minio-cold:
  volumes:
    - /data_archive:/data  # 替换 cold-data
```

---

## 📁 项目结构

```
├── docker-compose.yml        # 方案A：7容器一键部署
├── manage.sh                 # 方案A：管理脚本
├── single/                   # 方案A 完整配置
├── dual/                     # 方案B 完整配置
│   ├── deploy.sh · vm1-hot/ · vm2-cold/
│   ├── ilm/ · scripts/ · manual/
├── juicefs-offline/          # JuiceFS 离线安装包(34MB)
├── manual/                   # 完整部署手册 PDF
└── README.md
```

---

## 🔧 运维

```bash
# 单机
./manage.sh start|stop|status|logs

# 双机
cd dual && bash deploy.sh status-vm1|status-vm2

# MinIO
docker exec mc-init mc admin tier ls hot
docker exec mc-init mc du hot --recursive

# JuiceFS
juicefs status redis://VM-1-IP:6379/0
```

---

## 🔑 设计要点

| 决策 | 原因 |
|------|------|
| MinIO 单盘模式 | OneStor 底层已副本保护 |
| Redis 内置 | 为 JuiceFS 提供元数据引擎 |
| 1盘代替2盘 | 省50%容量，省EC计算CPU |

## 🔑 凭证

`radaradmin` / `RadarAdmin@2024!`

## 📄 完整手册

[雷达存储系统_完整部署手册.pdf](manual/雷达存储系统_完整部署手册.pdf)

# 📡 雷达数据存储系统

> 热数据 MinIO (NVMe) + 冷数据 MinIO (HDD) + Nginx 负载均衡 + 分层存储 + 自动生命周期管理

---

## 🚀 两种部署方案

### 方案 A：单虚拟机（测试 / 开发）

```
1 台 VM + 所有容器同机运行
```

```bash
git clone https://github.com/nriet/radar-storage-system.git
cd radar-storage-system

# 一键启动
./manage.sh start

# 访问
curl http://localhost:9010/minio/health/live    # MinIO 热
curl http://localhost:9020/minio/health/live    # MinIO 冷
curl http://localhost:18080                     # Nginx 代理
curl http://localhost:8888/health               # 监控面板
```

| VM 规格 | 端口 |
|---------|------|
| 4核 / 16G | 9010(热S3) · 9020(冷S3) · 18080(Nginx) · 8888(监控) |

---

### 方案 B：双虚拟机（生产环境）

```
VM-1: 热节点 (MinIO + Nginx + 监控)    4核/16G
VM-2: 冷节点 (MinIO 纯存储)            4核/8G
```

```bash
cd radar-storage-system/dual

# ---- VM-1 上执行 ----
bash deploy.sh vm1

# ---- VM-2 上执行 ----
bash deploy.sh vm2

# ---- 回到 VM-1，初始化分层连接 ----
export COLD_NODE_IP=<VM-2的IP地址>
bash deploy.sh init
```

---

## 📋 架构对比

| | 方案A（单机） | 方案B（双机） |
|------|-----------|-----------|
| 适用 | 测试/开发 | 生产环境 |
| 部署复杂度 | ⭐ 一条命令 | ⭐⭐ 两台VM |
| 热冷隔离 | ❌ 同机 | ✅ 物理隔离 |
| 容量 | Docker Volume | NVMe + HDD 直挂 |

---

## 🔄 数据流

```
雷达 → Nginx(18080) → MinIO热(NVMe) → ILM 7天 → MinIO冷(HDD)
                                           └ 90天过期删除
```

---

## 📁 项目结构

```
├── docker-compose.yml          # 单机方案（根目录直接启动）
├── manage.sh                   # 单机管理脚本
├── single/                     # 单机方案完整文件
│   ├── nginx.conf
│   ├── ilm/                    # ILM 策略
│   └── scripts/               # 初始化 · 模拟器 · 监控
├── dual/                       # 双机方案
│   ├── deploy.sh
│   ├── vm1-hot/               # VM-1 docker-compose
│   ├── vm2-cold/              # VM-2 docker-compose
│   ├── ilm/
│   ├── scripts/
│   └── manual/                # 安装手册 PDF
└── README.md
```

---

## ⚙️ 管理命令

```bash
# 单机
./manage.sh start|stop|status|logs

# 双机
cd dual
bash deploy.sh vm1|vm2|init|status-vm1|status-vm2|logs-vm1|logs-vm2
```

---

## 🔑 默认凭证

`radaradmin` / `RadarAdmin@2024!`

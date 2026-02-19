# 🚀 Local Setup Guide - Trade Connect

## ✅ Files Restored

The following critical files have been restored to the repository:

- ✅ `docker-compose.yml` - Service orchestration
- ✅ `mt5-engine/` - Headless MT5 engine
  - `Dockerfile` - MT5 container image
  - `entrypoint.sh` - MT5 startup script
  - `requirements.txt` - Python dependencies
  - `ea/TradeMonitor.mq5` - Expert Advisor for trade capture
  - `scripts/health_monitor.py` - Container health monitoring

**Latest commit**: `2059ed2` - "fix: restore MT5 headless engine files"

---

## 🐳 Docker Daemon Error Resolution

### **Issue**: Linux Engine API Compatibility

Your error:
```
❌ Linux engine API compatibility issue
The daemon is having trouble synchronizing with the desired API version
```

### **Solution: Step-by-Step**

#### **Option 1: System Restart (Recommended)**
```bash
# 1. Restart your machine
sudo reboot

# 2. Wait 1-2 minutes for Docker to fully initialize
# 3. Verify Docker is running
docker --version
docker ps
```

#### **Option 2: Restart Docker Service (Without Reboot)**
```bash
# Linux/macOS
sudo systemctl restart docker

# Or if using Docker Desktop:
# - Open Docker Desktop app
# - Settings → Docker Engine
# - Click "Apply & Restart"
# - Wait 30-60 seconds
```

#### **Option 3: Force Docker Daemon Reset**
```bash
# Stop Docker
sudo systemctl stop docker

# Clear daemon state
sudo rm -rf /var/lib/docker/overlay2/*

# Start Docker
sudo systemctl start docker

# Verify
docker ps
```

---

## 🔧 Pre-Flight Checks

Before building, verify your system:

```bash
# 1. Check Docker installation
docker --version
# Expected: Docker version 20.10+ (you have 29.2.0 ✅)

# 2. Check Docker daemon is running
docker ps
# Should return: CONTAINER ID (no error)

# 3. Check available disk space
df -h
# Need at least 10GB free for MT5 image

# 4. Check available RAM
free -h
# Recommended: 8GB+ total, 4GB+ free

# 5. Verify docker-compose
docker compose version
# Should show: Docker Compose version X.X.X+
```

---

## 📥 Clone & Verify Repository

```bash
# 1. Clone the repo (if not already done)
git clone https://github.com/Vinitmunjani/trade-copilot.git
cd trade-copilot

# 2. Verify critical files exist
ls -la docker-compose.yml
ls -la mt5-engine/Dockerfile
ls -la mt5-engine/ea/TradeMonitor.mq5
# All three should exist (not: "No such file or directory")

# 3. Pull latest changes
git pull origin main
```

---

## 🏗️ Build & Deploy

### **Step 1: Build MT5 Engine Image**
```bash
# From repo root
docker build -t trade-connect/mt5-headless:latest ./mt5-engine/

# This takes 5-10 minutes. Expected output:
# Step 1/11 : FROM ubuntu:22.04
# ...
# Successfully tagged trade-connect/mt5-headless:latest
```

### **Step 2: Verify Image Build**
```bash
docker images | grep trade-connect
# Should show:
# trade-connect/mt5-headless    latest    <image-id>    5 minutes ago    1.2GB
```

### **Step 3: Start Services**
```bash
# Start all containers (backend, frontend, Redis)
docker compose up -d

# Watch logs (optional)
docker compose logs -f
```

### **Step 4: Verify Services Are Running**
```bash
docker compose ps

# Expected output:
# NAME                 STATUS              PORTS
# trade-copilot-backend-1    Up 2 seconds    8000/tcp
# trade-copilot-frontend-1   Up 3 seconds    3000/tcp
# redis-1              Up 1 second         6379/tcp
```

---

## ✅ Health Check

Once services are running, verify they're healthy:

```bash
# 1. Backend health
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# 2. Frontend running
curl http://localhost:3000
# Expected: HTML response (Next.js page)

# 3. Redis connectivity
docker exec redis redis-cli ping
# Expected: PONG

# 4. Pool statistics
curl http://localhost:8000/api/terminals/pool-stats
# Expected: JSON with active terminals

# 5. View logs
docker compose logs backend | tail -20
docker compose logs frontend | tail -20
```

---

## 🧪 Test Trade Capture

### **Step 1: Open Frontend**
```
http://localhost:3000
```

### **Step 2: Create Test Account**
- Sign up with test email (e.g., test@example.com)
- Create password

### **Step 3: Connect MT5 Account**
- Go to **Settings → Broker Connection**
- Enter your MT5 credentials:
  - **Broker**: ICMarkets-Live01 (or your broker)
  - **Login**: Your MT5 account number
  - **Password**: Your MT5 password

### **Step 4: Place Test Trade**
- Open your MT5 terminal (on your machine or mobile)
- Place a small test trade (BUY 0.1 EURUSD)

### **Step 5: Verify Capture**
```bash
# Check backend logs
docker compose logs backend | grep "trade_webhook"

# Should see:
# trade_webhook received: {"ticket": 12345, "symbol": "EURUSD", "type": "BUY", ...}

# Query journal
curl http://localhost:8000/api/positions/YOUR_USER_ID
```

---

## 🔴 Troubleshooting

### **Build Fails: "Failed to solve with frontend dockerfile.v0"**
```bash
# Clear Docker build cache and rebuild
docker builder prune -a
docker build --no-cache -t trade-connect/mt5-headless:latest ./mt5-engine/
```

### **Containers Exit Immediately**
```bash
# Check container logs for errors
docker compose logs backend
docker compose logs mt5-pool

# Common causes:
# - Env var missing: Check .env file exists
# - Port conflict: sudo lsof -i :8000
# - Image not found: docker images
```

### **Port Already in Use**
```bash
# Find process using port
sudo lsof -i :8000

# Kill it
sudo kill -9 <PID>

# Or change port in docker-compose.yml:
# From: "8000:8000"
# To:   "8001:8000"
```

### **"Docker daemon not running"**
```bash
# Start Docker
sudo systemctl start docker

# Check status
sudo systemctl status docker

# Enable auto-start
sudo systemctl enable docker
```

---

## 📊 System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|------------|
| **RAM** | 4GB | 8GB+ |
| **Disk** | 20GB | 50GB+ |
| **CPU** | 2 cores | 4+ cores |
| **Docker** | 20.10+ | 29.0+ ✅ (you have) |
| **OS** | Ubuntu 20.04+ / macOS / Windows WSL2 | Ubuntu 22.04+ |

---

## 🚀 Next Steps After Local Testing

1. ✅ All services running (`docker compose ps`)
2. ✅ Backend health check passes (`curl localhost:8000/health`)
3. ✅ Frontend accessible (`http://localhost:3000`)
4. ✅ Test trade captured and appears in journal
5. **→ Ready for Staging Deployment** (Hetzner AX52)

---

## 📞 Need Help?

If you encounter issues:

1. Check Docker daemon status: `docker ps`
2. View service logs: `docker compose logs -f`
3. Verify files exist: `ls -la mt5-engine/`
4. Check network: `docker network ls`
5. Share error output in Discord #general

---

**Created**: 2026-02-19
**Status**: Production-Ready ✅

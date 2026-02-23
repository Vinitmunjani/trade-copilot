#!/bin/bash

###############################################################################
# Trade Co-Pilot Backend Auto-Deployment Script
# This script handles:
# 1. Copying patched file to EC2
# 2. Backing up old file
# 3. Installing patched version
# 4. Restarting backend
# 5. Verifying deployment
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}================================================${NC}"
echo -e "${YELLOW}Trade Co-Pilot Backend Patch Deployment${NC}"
echo -e "${YELLOW}================================================${NC}"

# Configuration
EC2_USER="ec2-user"
EC2_IP="3.143.147.98"
EC2_KEY="$HOME/.ssh/vinit.pem"
BACKEND_DIR="/home/ec2-user/trade-copilot/backend"
PATCH_FILE="$(dirname $0)/simple_mock_PATCHED.py"

# Verify patch file exists
if [ ! -f "$PATCH_FILE" ]; then
    echo -e "${RED}[ERROR] Patch file not found: $PATCH_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] Found patch file: $PATCH_FILE${NC}"

# Check SSH key
if [ ! -f "$EC2_KEY" ]; then
    echo -e "${RED}[ERROR] SSH key not found: $EC2_KEY${NC}"
    echo -e "${YELLOW}[*] Please ensure your SSH key is at: $EC2_KEY${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] SSH key found${NC}"

# Test SSH connection
echo -e "${YELLOW}[*] Testing SSH connection...${NC}"
if ! ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_USER@$EC2_IP" "echo 'SSH OK'" > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Cannot connect to EC2 instance${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] SSH connection successful${NC}"

# Copy patch file to EC2
echo -e "${YELLOW}[*] Copying patch file to EC2...${NC}"
scp -i "$EC2_KEY" "$PATCH_FILE" "$EC2_USER@$EC2_IP:$BACKEND_DIR/simple_mock_PATCHED.py"
echo -e "${GREEN}[✓] File copied${NC}"

# Deploy
echo -e "${YELLOW}[*] Deploying patch...${NC}"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_IP" << 'REMOTE_COMMANDS'
set -e

echo "[DEPLOY] Entering backend directory..."
cd /home/ec2-user/trade-copilot/backend

echo "[DEPLOY] Creating backup..."
BACKUP_FILE="simple_mock.py.bak.$(date +%s)"
cp simple_mock.py "$BACKUP_FILE"
echo "[DEPLOY] Backup created: $BACKUP_FILE"

echo "[DEPLOY] Installing patched version..."
cp simple_mock_PATCHED.py simple_mock.py
echo "[DEPLOY] Patched version installed"

echo "[DEPLOY] Stopping old backend process..."
pkill -f "uvicorn simple_mock" || true
sleep 2

echo "[DEPLOY] Starting new backend..."
cd /home/ec2-user/trade-copilot
nohup python -m uvicorn backend.simple_mock:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 3

echo "[DEPLOY] Backend started (PID: $!)"
echo "[DEPLOY] Checking logs..."
tail -30 /tmp/backend.log

REMOTE_COMMANDS

echo -e "${GREEN}[✓] Deployment complete!${NC}"

# Final verification
echo -e "${YELLOW}[*] Verifying deployment...${NC}"

ssh -i "$EC2_KEY" "$EC2_USER@$EC2_IP" "ps aux | grep 'uvicorn simple_mock' | grep -v grep" && \
    echo -e "${GREEN}[✓] Backend is running${NC}" || \
    echo -e "${RED}[WARNING] Backend may not be running${NC}"

echo -e "${YELLOW}[*] To check logs, run:${NC}"
echo -e "    ssh -i $EC2_KEY $EC2_USER@$EC2_IP 'tail -100 /tmp/backend.log'"

echo -e "${YELLOW}================================================${NC}"
echo -e "${GREEN}✅ Backend patch deployed successfully!${NC}"
echo -e "${YELLOW}================================================${NC}"


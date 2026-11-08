#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Deploying AegisBox (Blast Radius Zero) on Vultr VM"
echo "=========================================================="

# 1. Update packages and install prerequisites
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git curl docker.io docker-compose-v2

# 2. Ensure Docker service is running
systemctl enable --now docker

# 3. Clone or update repository in /opt/aegisbox
DEPLOY_DIR="/opt/aegisbox"
if [ -d "$DEPLOY_DIR" ]; then
    echo "Updating existing AegisBox repository..."
    cd "$DEPLOY_DIR"
    git pull origin master
else
    echo "Cloning AegisBox repository..."
    git clone https://github.com/Modeste01/aegisbox.git "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# 4. Build and start containers
echo "Starting AegisBox containerized stack..."
docker compose down --remove-orphans || true
docker compose up -d --build

# 5. Output public reachability
PUBLIC_IP=$(curl -s -m 5 https://ifconfig.me || echo "144.202.31.205")
echo "=========================================================="
echo "  AegisBox is LIVE and fully operational!"
echo "  Web Console: http://${PUBLIC_IP}:8000"
echo "=========================================================="

#!/bin/bash
# Deploy Agent Hub to a Proxmox node
# Usage: ./scripts/deploy.sh <node-ip>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

NODE_IP="${1:?Usage: deploy.sh <node-ip>}"
REMOTE_DIR="/opt/agenthub"

echo "Deploying to $NODE_IP..."

# Sync repo to server
rsync -avz --exclude='.git' --exclude='.env' \
  "$REPO_ROOT/" "root@$NODE_IP:$REMOTE_DIR/"

# Pull and restart containers
ssh "root@$NODE_IP" bash -s <<'EOF'
  cd /opt/agenthub/homelab
  docker compose pull
  docker compose up -d --build
  docker compose ps
EOF

echo "Deploy complete."

#!/bin/bash
# Open SSH tunnels for local debugging
# Usage: ./scripts/ssh-tunnel.sh <node-ip>

NODE_IP="${1:?Usage: ssh-tunnel.sh <node-ip>}"

echo "Opening tunnels to $NODE_IP..."
echo "  Postgres → localhost:5433"
echo "  Redis    → localhost:6380"
echo "Press Ctrl+C to close."

ssh -N -L 5433:localhost:5432 \
       -L 6380:localhost:6379 \
  "root@$NODE_IP"

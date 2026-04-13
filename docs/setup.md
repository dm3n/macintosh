# Setup Guide

## Prerequisites

- 2-node Proxmox cluster running
- Docker + Docker Compose installed on target node
- SSH access to both nodes
- GitHub account (dm3n)
- Google Cloud project with Gmail, Calendar, Tasks APIs enabled
- Telegram account

---

## Step 1 — Telegram Bot

1. Open Telegram → message **@BotFather**
2. Send `/newbot`
3. Name: `Airbank Hub` / Username: `airbank_hub_bot` (or similar)
4. Copy the **bot token** → `TELEGRAM_BOT_TOKEN` in `.env`
5. Message **@userinfobot** to get your personal chat ID → `TELEGRAM_OWNER_CHAT_ID`

---

## Step 2 — Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create or select a project
3. Enable APIs:
   - Gmail API
   - Google Calendar API
   - Google Tasks API
4. Create **OAuth 2.0 credentials** (Desktop app type)
5. Copy Client ID + Secret → `.env`
6. Complete OAuth consent and capture the refresh token for your user.
7. Store values in `homelab/.env`:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`

---

## Step 3 — GitHub Token

1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained
2. Scopes: `Contents` (read/write), `Pull requests` (read/write), `Metadata` (read)
3. Copy → `GITHUB_TOKEN` in `.env`

---

## Step 4 — Deploy to Server

```bash
# SSH into primary node
ssh root@<node1-ip>

# Clone repo
git clone https://github.com/dm3n/macintosh.git /opt/agenthub
cd /opt/agenthub/homelab

# Copy and fill in env
cp .env.example .env
nano .env  # fill in all values

# Start stack
docker compose up -d

# Watch logs
docker compose logs -f hub-orchestrator
```

---

## Step 5 — Verify

```bash
# Check all containers running
docker compose ps

# Check orchestrator logs
docker compose logs -f hub-orchestrator

# Check DB schema applied
docker compose exec hub-db psql -U agenthub -d agenthub -c "\dt"
```

---

## Node 2 (Standby)

```bash
ssh root@<node2-ip>
git clone https://github.com/dm3n/macintosh.git /opt/agenthub
cd /opt/agenthub/homelab
cp .env.example .env
# Copy same .env values from node1
# Do NOT start — standby only
# To failover: docker compose up -d
```

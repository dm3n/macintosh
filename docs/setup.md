# Setup Guide

## Prerequisites

- 2-node Proxmox cluster (or single-node test target)
- Docker + Docker Compose on target node
- SSH access
- GitHub account access
- Google Cloud APIs enabled (Gmail, Calendar, Tasks)
- Linear API key + team/project access for approval workflow

## Step 1 — Clone + Environment

```bash
git clone https://github.com/dm3n/macintosh.git /opt/agenthub
cd /opt/agenthub/homelab
cp .env.example .env
```

Populate `.env` with:
- AI keys
- DB credentials
- GitHub token
- Google OAuth credentials
- Linear keys (`LINEAR_API_KEY`, `LINEAR_TEAM_ID`)
- Slack bot credentials (if used)

## Step 2 — Google OAuth

1. Create OAuth desktop credentials in GCP
2. Enable Gmail/Calendar/Tasks APIs
3. Store:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`

## Step 3 — Bring Stack Up

```bash
cd /opt/agenthub/homelab
docker compose up -d --build
docker compose ps
```

## Step 4 — Verify

```bash
# schema loaded
docker compose exec hub-db psql -U agenthub -d agenthub -c "\dt"

# orchestrator healthy
docker compose logs -f hub-orchestrator
```

## Standby Node

```bash
ssh root@<node2-ip>
git clone https://github.com/dm3n/macintosh.git /opt/agenthub
cd /opt/agenthub/homelab
cp .env.example .env
# keep in standby until failover
```

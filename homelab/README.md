# Homelab Runtime

This directory contains the runtime stack for Macintosh automation.

## Files

- `docker-compose.yml` — full runtime service graph
- `.env.example` — required configuration keys
- `database/schema.sql` — state and audit schema
- `scripts/deploy.sh` — remote deployment helper
- `scripts/ssh-tunnel.sh` — local debugging tunnels

## Approval System

Approvals are Linear-based.

Required env keys:
- `LINEAR_API_KEY`
- `LINEAR_TEAM_ID`
- `LINEAR_APPROVAL_PROJECT_ID`

Runtime approval path:
- agents create `pending_actions`
- approval gateway syncs to Linear
- approved actions trigger executor delivery

## Bring Up Locally

```bash
cd homelab
cp -n .env.example .env
# fill required credentials
docker compose up -d --build
```

## Verification

```bash
docker compose ps
docker compose logs -f hub-orchestrator
docker compose logs -f hub-approval
```

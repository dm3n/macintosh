# Homelab Architecture

> Infrastructure-first view of the Macintosh homelab.

## Platform First

Homelab is primarily the server platform:
- **Proxmox** for virtualization/host management
- **Casa** for service management and operator UX
- **Docker** for current container workloads
- **Kubernetes** as part of the same homelab compute strategy

The agent runtime is one workload set running on top of this platform.

## Layered Homelab Model

```text
Physical server(s)
  -> Proxmox virtualization layer
  -> Casa management layer
  -> Container orchestration (Docker today, Kubernetes in-platform)
  -> Workloads (automation services, data services, support services)
```

## Macintosh Automation Workload (Current)

Current workload graph inside the homelab platform:
- `hub-db` (Postgres)
- `hub-redis` (queue/event bus)
- `hub-mcp` (integration abstraction)
- `hub-orchestrator` (dispatch/scheduling)
- `hub-approval` (Linear approval sync)
- `hub-executor` (approved action delivery)
- domain agents (`code`, `email`, `calendar`, `linear`, `slack`, `todo`)

## Approval and Control

- system of record for approvals: **Linear**
- agents produce pending actions only
- executor delivers only approved actions
- lifecycle tracked in `pending_actions` and `audit_log`

Action status model:

```text
pending -> approved/rejected -> delivered/failed
```

## Data and Security

- state in Postgres (`homelab/database/schema.sql`)
- queue/event signaling in Redis
- secrets in `homelab/.env` only
- no direct external writes from agent workers
- internal Docker network isolation for runtime services

## Deploy / Operate

```bash
# from repo root
./homelab/scripts/deploy.sh <node-ip>

# debug tunnels
./homelab/scripts/ssh-tunnel.sh <node-ip>
```

Remote compose root:
- `/opt/agenthub/homelab`

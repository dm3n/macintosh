# Homelab Architecture

> Runtime architecture for the Macintosh automation system.

## Core Principle

Agents draft. Humans approve in Linear. Executor delivers.

No agent writes directly to external systems.

## End-to-End Flow

```text
Trigger (cron/webhook/manual)
  -> Orchestrator dispatches runtime job
  -> Agent generates pending action in Postgres
  -> Approval Gateway syncs action into Linear approvals workflow
  -> Human decision in Linear (Approved/Rejected)
  -> Approval Gateway updates action status
  -> Executor consumes approved actions
  -> Delivery result logged to audit trail
```

## Compose Service Map

| Compose Service | Purpose | Port/Dependency Notes |
|---|---|---|
| `hub-db` | Postgres state store | stores jobs, pending actions, audit logs |
| `hub-redis` | queue/event bus | pub/sub backbone |
| `hub-mcp` | integration abstraction | internal service for tool handlers |
| `hub-orchestrator` | scheduling + dispatch | references `LINEAR_API_KEY`, `LINEAR_TEAM_ID` |
| `hub-approval` | Linear approval synchronization | references `LINEAR_APPROVAL_PROJECT_ID` |
| `hub-executor` | approved action delivery | consumes `actions:approved` events |
| `hub-agent-code` | code-domain agent | scheduled worker |
| `hub-agent-email` | email-domain agent | scheduled worker |
| `hub-agent-calendar` | calendar-domain agent | scheduled worker |
| `hub-agent-linear` | linear-domain agent | scheduled worker |
| `hub-agent-slack` | slack-domain agent | scheduled worker |
| `hub-agent-todo` | todo-domain agent | scheduled worker |

## Data Backbone

Primary tables in `homelab/database/schema.sql`:
- `agents`
- `jobs`
- `pending_actions`
- `agent_memory`
- `audit_log`
- `morning_reports`

Action statuses:

```text
pending -> approved/rejected -> delivered/failed
```

## Approval Model (Current)

- Approval system of record: **Linear**
- Approval Gateway maps Linear decisions to `pending_actions.status`
- Executor processes only `approved` actions

Required approval env keys:
- `LINEAR_API_KEY`
- `LINEAR_TEAM_ID`
- `LINEAR_APPROVAL_PROJECT_ID`

## Security and Control

- secrets live in `homelab/.env`
- internal service networking only (`hub` bridge network)
- no direct external writes from agents
- full audit trail for every action lifecycle transition

## Deploy / Operate

```bash
# from repo root
./homelab/scripts/deploy.sh <node-ip>

# debug tunnels
./homelab/scripts/ssh-tunnel.sh <node-ip>
```

Compose root on remote host:
- `/opt/agenthub/homelab`

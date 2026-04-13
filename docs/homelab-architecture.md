# Homelab Architecture

> Part of [dm3n/macintosh](https://github.com/dm3n/macintosh)

## Core Principle

Every agent is a drafter, not a doer.
Agents create pending actions; execution only happens after approval in **Linear**.

## Runtime Data Flow

```text
External trigger (cron/webhook/manual)
  -> Orchestrator decides agent dispatch
  -> Agent produces pending action in Postgres
  -> Approval Gateway syncs pending action to Linear
  -> Human approves/rejects in Linear
  -> Executor consumes approved action
  -> Delivery status and audit log recorded
```

## Services

- Orchestrator: schedules and dispatches work
- MCP Gateway: integration tool abstraction
- Approval Gateway: syncs pending actions with Linear approval states
- Executor: delivers approved actions
- Agents: code/email/calendar/linear/slack/todo
- Postgres + Redis: queue/state/audit backbone

## Approval States

```sql
pending   -> waiting for decision
approved  -> execution allowed
rejected  -> discarded
delivered -> executor completed
failed    -> executor attempted and failed
```

## Security Model

- secrets in `.env` only
- no direct agent writes to external systems
- executor-only delivery path
- audited status transitions for every action
- private infrastructure access via SSH/Tailscale

## Deployment

```bash
# Deploy to primary node
./homelab/scripts/deploy.sh <node-ip>

# SSH tunnel for debug
./homelab/scripts/ssh-tunnel.sh <node-ip>
```

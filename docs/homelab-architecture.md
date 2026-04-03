# Homelab Architecture

> Part of [dm3n/macintosh](https://github.com/dm3n/macintosh) — the complete engineering OS.

## Core Principle

Every agent is a **drafter, not a doer**. Agents work autonomously, produce outputs, and queue them as pending approvals. The executor only runs after explicit human approval via Telegram.

This means:
- Agents can run aggressively without risk
- Nothing touches production, inboxes, or calendars without consent
- Full audit trail of every action taken or rejected

---

## Data Flow

```
External trigger (cron / webhook / Telegram message)
        ↓
Orchestrator receives + decides which agent(s) to invoke
        ↓
Agent runs Claude API with tools (read-only + draft tools)
        ↓
Agent produces PendingAction record in Postgres
        ↓
Orchestrator sends Telegram notification with inline buttons
        ↓
User approves or rejects on Telegram (or morning report queue)
        ↓
Executor receives approved action → delivers via appropriate API
        ↓
Action logged as completed in Postgres
```

---

## Orchestrator

The central brain. Responsibilities:

1. **Receives inputs**: Telegram messages, cron triggers, webhook events
2. **Dispatches to agents**: Pushes jobs onto Redis queue for the right agent
3. **Aggregates outputs**: Polls pending actions, bundles for morning report
4. **Manages Telegram**: Handles all bot interactions, sends/receives messages
5. **Tracks state**: Knows what each agent last did and when

The orchestrator uses Claude with a high-level system prompt. It doesn't do domain work itself — it delegates.

**Morning report cron**: `0 7 * * *` (7:00 AM daily)

---

## Agent Design

Each agent follows the same interface:

```typescript
interface AgentJob {
  jobId: string
  agentType: 'code' | 'email' | 'calendar' | 'todo'
  trigger: 'cron' | 'webhook' | 'manual'
  context?: Record<string, unknown>
}

interface PendingAction {
  id: string
  agentType: string
  actionType: string          // 'github_pr' | 'send_email' | 'create_event' | etc.
  summary: string             // 1-2 sentence human-readable description
  fullOutput: string          // Full agent output (shown on "View" tap)
  payload: Record<string, unknown>  // Executor uses this to deliver
  status: 'pending' | 'approved' | 'rejected' | 'delivered' | 'failed'
  createdAt: Date
  approvedAt?: Date
  deliveredAt?: Date
}
```

Each agent has:
- A Claude system prompt defining its role and constraints
- A set of **read-only tools** (read files, read emails, read calendar, etc.)
- A **draft tool** that creates a PendingAction (never writes directly)
- Access to its own memory namespace in Postgres

---

## MCP Gateway

A single MCP server process that exposes all external integrations as tools.
All agents connect to it rather than integrating APIs individually.

MCP tools exposed:

```
# Filesystem (read-only for agents, write only via executor)
fs_read_file(path)
fs_list_dir(path)
fs_search(pattern)

# GitHub (read + draft)
github_list_prs(repo)
github_get_file(repo, path)
github_search_code(repo, query)
github_draft_pr(repo, branch, title, body, changes) → PendingAction

# Gmail (read + draft)
gmail_list_threads(query, maxResults)
gmail_read_thread(threadId)
gmail_draft_reply(threadId, body) → PendingAction
gmail_draft_new(to, subject, body) → PendingAction

# Google Calendar (read + draft)
gcal_list_events(calendarId, timeMin, timeMax)
gcal_get_event(calendarId, eventId)
gcal_draft_event(calendarId, summary, start, end, ...) → PendingAction
gcal_draft_update(calendarId, eventId, changes) → PendingAction

# Google Tasks (read + draft)
gtasks_list_tasks(taskListId)
gtasks_get_task(taskListId, taskId)
gtasks_draft_task(taskListId, title, notes, due) → PendingAction
gtasks_draft_update(taskListId, taskId, changes) → PendingAction
```

All `*_draft_*` tools write a PendingAction to Postgres and return its ID.
The executor is the only service with write access to external APIs.

---

## Approval System

### Telegram Approval Message Format

```
🤖 Code Agent — 2 PRs ready

1. Fix: Cell PATCH validation bug in /api/workbooks/[id]/cells/[cellId]
2. Add: Missing test coverage for /api/workbooks/[id]/flags

[✅ Approve All]  [❌ Reject All]  [👁 Review Each]
```

Individual review:
```
PR #1 — Fix: Cell PATCH validation bug

The cell PATCH route had an impossible condition
(raw_value === undefined && raw_value !== null).
Fixed to: raw_value === undefined

Branch: fix/cell-patch-validation
Files changed: app/api/workbooks/[id]/cells/[cellId]/route.ts

[✅ Approve]  [❌ Reject]  [⏭ Skip]
```

### Approval States

```sql
pending   → waiting for user decision
approved  → user approved, executor will deliver
rejected  → user rejected, action discarded
delivered → executor successfully delivered
failed    → executor attempted delivery but failed (retries available)
```

---

## Executor

Runs as an event-driven service. Listens on Redis for `action:approved` events.

Executor handlers:

| actionType | What the executor does |
|---|---|
| `github_pr` | Creates branch, commits changes, opens PR via GitHub API |
| `send_email` | Sends via Gmail API (from OAuth token) |
| `create_event` | Creates event via Google Calendar API |
| `update_event` | Updates existing event |
| `create_task` | Creates task via Google Tasks API |
| `update_task` | Updates existing task |

---

## Database Schema

See `database/schema.sql` for full definitions.

Key tables:
- `agents` — registered agents and their last-run metadata
- `jobs` — agent job history
- `pending_actions` — the approval queue
- `agent_memory` — per-agent key/value store for context persistence
- `audit_log` — every approval, rejection, and delivery

---

## Security Considerations

- All API keys in `.env` file, never committed
- Servers accessible only via SSH (no public ports for admin services)
- Postgres and Redis not exposed outside Docker network
- MCP Gateway bound to internal Docker network only
- Telegram bot validates chat_id matches configured owner ID
- Google OAuth tokens stored encrypted in Postgres

---

## Cluster Deployment

Both Proxmox nodes run the same Docker stack.
Node 1 is primary; Node 2 is warm standby (manual failover for now).

```bash
# Deploy to primary node
./scripts/deploy.sh node1

# SSH tunnel for local debugging
./scripts/ssh-tunnel.sh node1
```

Future: Portainer or Nomad for proper cluster orchestration.

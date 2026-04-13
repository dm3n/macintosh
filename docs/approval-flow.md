# Approval Flow

## Rule

No agent sends, schedules, writes, or updates external systems without explicit approval.

All approvals are managed in **Linear**.

## Approval Interface (Linear)

Agents create approval records as pending actions in Postgres.
The approval gateway syncs each pending action to Linear as an issue in the approvals project/team.

Suggested Linear issue template:
- Title: `[Approval] <action summary>`
- Labels: `approval`, `<agent>`, `<action-type>`
- Body sections:
  - Context
  - Proposed action payload
  - Risk notes
  - Rollback strategy

Decision mapping:
- Linear status `Approved` -> pending action becomes `approved`
- Linear status `Rejected` -> pending action becomes `rejected`

## Action Types

| Action | Approval medium | Delivery |
|---|---|---|
| Code change | GitHub PR + Linear approval | GitHub merge / executor follow-up |
| Send email | Linear approval issue | Executor via Gmail API |
| Create calendar event | Linear approval issue | Executor via Calendar API |
| Update calendar event | Linear approval issue | Executor via Calendar API |
| Create task | Linear approval issue | Executor via Tasks API |
| Update task | Linear approval issue | Executor via Tasks API |

## Audit Trail

Every approval event is logged in `audit_log`.

```sql
SELECT a.summary, a.status, a.agent_id, a.decided_at
FROM pending_actions a
ORDER BY a.created_at DESC
LIMIT 20;
```

Status lifecycle:
- `pending`
- `approved` / `rejected`
- `delivered` / `failed`

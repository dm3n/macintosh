# Approval Flow

## The Rule

**No agent writes, sends, schedules, or merges anything without your approval.**

Agents have read access to everything. Write access belongs exclusively to the Executor, which only runs after you tap Approve.

---

## Approval Interface

All approvals happen in Telegram.

### Batched (default for morning report)

```
🤖 Email Agent — 3 draft replies ready

1. Re: Q1 investor update → Sarah Chen
2. Re: Partnership intro → Marcus (Stripe)
3. FWD: Legal docs → your lawyer

[✅ Approve All]  [❌ Reject All]  [👁 Review Each]
```

### Individual review

```
Draft reply #1

To: Sarah Chen
Subject: Re: Q1 investor update

---
Hi Sarah,

Thanks for checking in. The Q1 numbers are looking strong —
ARR up 40% QoQ. Happy to jump on a call this week to walk
through the details. Does Thursday 3pm work?

Best,
Daniel
---

[✅ Send]  [❌ Reject]  [✏️ Edit]  [⏭ Next]
```

### Code PRs

For code changes, the agent opens a real GitHub PR. You review it normally in GitHub and merge when ready. The Telegram message just links to it:

```
🧑‍💻 Code Agent — PR ready for review

Fix: Cell PATCH validation bug
Branch: fix/cell-patch-validation

View on GitHub → github.com/dm3n/qoe-platform/pull/42

[❌ Close PR]
```

---

## Action Types

| Action | How approval works | Who delivers |
|---|---|---|
| Code change | GitHub PR opened, you merge | GitHub (you) |
| Send email | Telegram inline → Approve | Executor via Gmail API |
| Create calendar event | Telegram inline → Approve | Executor via Calendar API |
| Update calendar event | Telegram inline → Approve | Executor via Calendar API |
| Create task | Telegram inline → Approve | Executor via Tasks API |
| Update task | Telegram inline → Approve | Executor via Tasks API |

---

## Audit Trail

Every action is logged in the `audit_log` table regardless of outcome:

```sql
SELECT a.summary, a.status, a.agent_id, a.decided_at
FROM pending_actions a
ORDER BY a.created_at DESC
LIMIT 20;
```

You can always see exactly what agents did, drafted, and what you approved or rejected.

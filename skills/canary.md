---
name: canary
description: Plan and execute a canary release for a high-risk feature. Define rollout stages, monitoring checkpoints, and a clear rollback path before anything ships to production.
---

# Canary — Staged Release Planning

Ship to a small group first. Catch production-only issues before they affect everyone. This is for features that are too risky to flip all at once.

## When to Use

- Auth flow changes (login, signup, session handling)
- Major data model changes (new columns, schema migrations)
- New third-party integrations (email providers, payment processors)
- Large rewrites of existing features
- Features with untested edge cases in production data

For small bug fixes and additive UI changes, a canary is overkill. Ship normally.

## Usage

```
/canary "Google OAuth integration"
/canary "new document processing pipeline"
/canary "document storage migration"
```

## Process

**1. Define the canary population**

Who sees this first? A typical staged population:
- **Stage 1:** Internal only (Daniel + any test accounts)
- **Stage 2:** Design partners / pilot customers, by feature flag or separate environment
- **Stage 3:** Full rollout

**2. Define the feature flag or gate**

How do you control who sees the new behavior?

Options for Next.js + Supabase:
- Environment variable toggle (`NEXT_PUBLIC_FEATURE_X=true`)
- User ID allowlist in a `feature_flags` table
- A/B split by user ID modulo
- Separate deployment (staging → production port)

Pick the simplest one that works. Complexity in the flag mechanism is itself a risk.

**3. Define success metrics**

What does "it's working" look like at each stage? Be specific:
- Error rate below X%
- P95 response time below Xms
- Zero auth failures for canary users
- Specific user actions completing successfully

**4. Define the rollback trigger**

What single event causes an immediate rollback? Write it down before you ship:
- Error rate exceeds X% for > Y minutes
- Any user reports complete inability to complete [core action]
- Data corruption detected

**5. Define the rollback procedure**

How do you get back to the previous state in under 5 minutes?
- Revert the feature flag / env var
- Roll back the deployment
- Run a compensating migration if data was affected

Write the exact commands. Don't figure this out under pressure.

## Output Format

```
Canary Plan — [feature] — [date]

Risk Level: High / Critical

Stage 1 — Internal (Day 1)
  Population: [who]
  Gate: [how they see it]
  Success: [metrics]
  Rollback trigger: [condition]
  Rollback steps: [commands]

Stage 2 — Design Partners (Day X)
  Population: [who]
  Promotion criteria: [what must be true to proceed]
  ...

Stage 3 — Full Rollout (Day X)
  Promotion criteria: [what must be true]
  Monitoring window: [how long before flag is cleaned up]

Rollback Commands:
  [exact commands, copy-paste ready]
```

After writing the plan, `careful` mode is automatically active for Stage 1 execution.

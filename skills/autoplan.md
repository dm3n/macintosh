---
name: autoplan
description: Auto-generate a complete implementation plan from a feature description. Combines product interrogation, architecture, and task breakdown in one flow. Outputs a ready-to-execute plan.
---

# Autoplan — Feature to Plan in One Command

Describe what you want to build. Get a complete, ready-to-execute implementation plan back. No back-and-forth — just the plan.

## Usage

```
/autoplan "add Google OAuth to the borrower portal"
/autoplan "build a debt schedule tab in the origination agent"
/autoplan "add email notifications when a document is uploaded"
```

## What This Does

Autoplan is the fast path when you already know what you want and don't need product interrogation. It:

1. Scopes the feature against the current codebase
2. Identifies every file that needs to change
3. Identifies risks and dependencies
4. Breaks work into discrete, parallelizable tasks
5. Writes the plan to a spec file

## Process

**1. Understand current state**

Read the relevant codebase sections before proposing anything. Explore:
- The files closest to what's being built
- Existing patterns to follow (don't invent new conventions)
- The DB schema and API routes already in place
- Recent commits that might conflict

**2. Define scope precisely**

For the requested feature, define:
- **What's in:** exactly what will exist after this is done
- **What's out:** adjacent things that are tempting but not needed now
- **Entry points:** where does the user access this feature?
- **Data model:** what's new in the DB, what changes?
- **API routes:** what new routes, or changes to existing routes?
- **UI:** what pages/components change?

**3. Identify all files to touch**

List every file that will change or be created. For Airbank projects this typically includes:
- `app/api/` — new or modified routes
- `app/` — page components
- `components/` — UI components
- `lib/` — utilities, types, client helpers
- `homelab/database/schema.sql` — if DB changes needed
- `homelab/.env.example` — if new env vars

**4. Identify risks**

What could go wrong?
- Breaking changes to existing API routes
- Supabase RLS changes that could expose data
- Auth flow changes that could lock users out
- SSE or realtime complexity
- Third-party API dependencies

**5. Write the plan**

Break the work into numbered tasks. Each task should be:
- Completable in one session
- Independently testable
- Clear about what done looks like

## Stack Rules (Always Apply)

- **UI:** shadcn/ui components only. Never raw HTML elements.
- **Auth:** `@supabase/ssr` with `createServerClient` in API routes, `createBrowserClient` in components. Never `@supabase/supabase-js` directly in Next.js pages.
- **Routing:** Next.js 16 App Router. `proxy.ts` not `middleware.ts`.
- **Forms:** react-hook-form + shadcn Form components + zod validation.
- **Env:** new vars go in `.env.example` with a comment.
- **DB:** all new tables get RLS enabled immediately.

## Output

Write the plan to `docs/plans/YYYY-MM-DD-[feature]-plan.md`.

Format:

```markdown
# [Feature Name] — Implementation Plan
Date: YYYY-MM-DD

## What We're Building
[2-3 sentence description]

## What's In / Out
In: ...
Out: ...

## Files to Touch
[list with reason]

## Risks
[list]

## Tasks

### Task 1: [name]
Files: ...
What to do: ...
Done when: ...

### Task 2: [name]
...
```

After writing the plan, execute it goal-driven: work one task at a time and run each task's verify check before moving on (per the karpathy guidelines).

---
name: careful
description: Activate careful mode before any risky operation — DB migrations, auth changes, RLS modifications, production deploys, destructive scripts. Forces explicit confirmation before proceeding.
---

# Careful — Risky Operation Protocol

Some changes cannot be undone. This skill forces the right level of deliberation before you make them.

## When to Invoke

Invoke automatically before:
- Any `ALTER TABLE`, `DROP TABLE`, or `DROP COLUMN` in a migration
- Any change to Supabase RLS policies
- Any change to auth flow (proxy.ts, Supabase auth config, session handling)
- Running a script that modifies or deletes production data
- Changing environment variables that affect running services
- Any `git reset --hard`, `git push --force`, or branch deletion
- Deploying to production without a staging test

## Process

**1. State the operation clearly**

Write out exactly what is about to happen in plain language. Not code — English sentences a non-engineer could understand.

Example:
> "I am about to remove the `sacred_secretion_cycles` table from the production database schema. This will permanently delete all data in that table and cannot be undone without a backup restore."

**2. Identify what could go wrong**

List every failure mode:
- What breaks if this goes wrong?
- Who is affected?
- Can it be reversed? How?
- Is there a backup or rollback path?

**3. Pre-flight checks**

Before proceeding:
- [ ] Is there a recent database backup? (check Supabase dashboard)
- [ ] Is the staging environment tested?
- [ ] Are any other changes in flight that could conflict?
- [ ] Does anyone else need to know about this change?

**4. Get explicit confirmation**

Do not proceed until the user explicitly says to. Present the summary and ask:

> "Ready to proceed? This will [plain-language description]. Type 'yes' to continue or 'no' to stop."

**5. Execute with observation**

Once confirmed, execute the operation. Watch for errors in real time. If anything unexpected happens, stop immediately and report.

**6. Verify success**

After the operation, verify the expected state. Don't assume it worked — check.

## Escape Hatch

If the operation cannot be reversed and something goes wrong, say so immediately. Don't try to fix it silently. Surface the problem to the user with:
- What happened
- What state the system is in now
- What the options are

## Airbank-Specific Checks

For database changes:
- All migrations are additive first (add columns before dropping old ones)
- RLS changes are tested with both `anon` and `authenticated` roles
- No migration touches both schema and data in the same statement

For auth changes:
- Always test login, signup, and session refresh after any auth modification
- Never change `proxy.ts` without testing the full session lifecycle

For production deploys:
- Verify `npm run build` passes locally before pushing
- Check that no `.env` keys are missing from production config

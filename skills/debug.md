---
name: debug
description: Systematic debugging discipline. Use when facing any bug, test failure, or unexpected behavior, before proposing a fix. Forces root-cause analysis over symptom patching.
---

# Debug: Root Cause Before Fix

The failure mode this prevents: patching the first symptom you see, guessing, or changing code you don't understand. Work the problem in order instead.

## The Loop

1. **Reproduce.** Get a reliable, minimal repro. If you cannot reproduce it, you cannot fix it. State the exact steps and the observed vs expected behavior.
2. **Isolate.** Narrow to the smallest failing surface. Bisect the change: comment out halves, log at boundaries, check recent commits. Find the line where reality diverges from expectation.
3. **Root cause.** Explain WHY it happens in one sentence, in terms of the actual mechanism. If you cannot state the cause, you have not found it. A fix without a cause is a guess.
4. **Minimal fix.** Change only what the cause requires (Surgical Changes). No drive-by refactors while debugging.
5. **Verify.** Re-run the original failing path and confirm it is gone. Check you did not break the neighbors.

## Rules

- One hypothesis at a time. Test it, confirm or kill it, then move on. Don't shotgun five changes at once.
- Tried three fixes and none worked? Stop. You are guessing. Go back to step 2 and isolate harder.
- Read the actual error and stack trace before theorizing. The answer is often in the message.
- Reproduce before fixing, verify after. No "this should work" without running it.

## Stack notes

- "Cannot find module ./chunks/vendor-chunks/*.js" means a prod build and the dev server corrupted `.next/`. Stop both, `rm -rf .next`, restart dev. Typecheck with `npx tsc --noEmit`, never `npm run build` while dev runs.
- Supabase RLS bugs: reproduce with both `anon` and `authenticated` roles. An empty result is often a policy, not a query bug.
- Hydration mismatches: find the server/client branch that differs, not the component that throws.

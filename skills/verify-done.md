---
name: verify-done
description: Evidence before claiming done. Use before saying work is complete, fixed, or passing, or before committing or opening a PR. Run the check, show the output, then claim success. The cross-agent verification discipline.
---

# Verify Done: Evidence Before Assertions

The rule: never claim something works until you have run the command and seen it pass. "Should work" is not "works." This is the cross-agent discipline: Claude Code has a built-in `/verify`, but this one also works in Codex, Gemini, and OpenCode, and is intentionally lighter.

## Before claiming done

1. Restate the success criterion in one line (from the request, or the Goal-Driven plan).
2. Run the actual check that proves it:
   - Typecheck: `npx tsc --noEmit` (while dev runs; never `npm run build` then).
   - Tests: run the suite or the specific test, and show the result.
   - Behavior: exercise the real flow (a `/qa` pass, a curl, a script run).
3. Show or summarize the real output. Evidence, not assertion.
4. If it failed, say so plainly with the output. A failed check reported honestly beats a false "done."

## Don't

- Don't claim "tests pass" without running them.
- Don't say "fixed" without reproducing the original failure and confirming it is gone (see `/debug`).
- Don't skip a step and call it complete. If you skipped verification, say which step and why.

## Commit / PR gate

Before a commit or PR: typecheck clean, relevant tests or flows verified, the diff contains only requested changes (Surgical Changes), and no AI attribution in the message.

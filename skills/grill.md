---
name: grill
description: Structured requirements interrogation before building. Run an interview loop that pushes on scope, edge cases, priorities, and what "done" means until the spec is sharp, then write the agreed contract to disk. Invoke before any non-trivial build, or when a request is ambiguous enough that guessing would be expensive.
---

# Grill: Requirements Interrogation

Misalignment is the most expensive failure mode: the agent builds the wrong thing well. The karpathy baseline says "state assumptions, ask if uncertain" — this skill is the procedure for doing that properly. It front-loads the questions so the build runs without mid-flight guessing, and it ends by writing the contract that the loops architecture grades against.

Adapted from Matt Pocock's `grill-me` / `grilling` skills into this setup's contract-first loop architecture.

## When to grill

- Any non-trivial build request (new feature, automation, integration, refactor with behavior change).
- Any request where two reasonable engineers would build different things.
- NOT for trivial tasks, direct unambiguous instructions, or bug fixes with a clear reproduction — direct execution applies there.

## The loop

Ask in rounds of at most 3-4 questions. One topic per question. Prefer concrete forced choices ("when X happens, should it A or B?") over open prompts ("any thoughts on X?"). Stop when a round produces no new constraints.

Cover, in rough order:

1. **Outcome** — what changes in the world when this works? Who uses it, how often, triggered by what?
2. **Scope boundary** — what is explicitly OUT? Name the adjacent things this does not do.
3. **Edge cases** — the empty case, the duplicate case, the failure case, the concurrent case, the stale-data case. For each: handle, reject, or ignore?
4. **Priorities** — if time runs short, what ships first? What is nice-to-have?
5. **Verification** — how will we both know it works? What would the user check by hand to trust it?
6. **Constraints** — stack rules, existing systems it must reuse, things it must not touch.

Push back during the interview: if an answer implies a simpler approach, say so. If two answers conflict, surface the conflict immediately instead of averaging them.

## The exit: write the contract

Grilling ends with a written artifact, not a feeling of clarity. Produce `contract.md` (or the project's equivalent) containing:

- One-paragraph outcome statement.
- Checklist of testable assertions (aim for enough that an evaluator can't rubber-stamp — see loops.md rule 3; ~10 for small tasks, ~27 for a small app).
- Explicit out-of-scope list.
- The verification step the human will run.

Get one confirmation on the contract, then build against it without further permission-seeking. The contract, not the conversation, is what gets graded.

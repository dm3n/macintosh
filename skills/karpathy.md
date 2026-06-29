---
name: karpathy
description: The engineering methodology baseline for every coding agent in this setup. Four behavioral principles (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution) that cut the common LLM coding failure modes. Apply when writing, reviewing, or refactoring any code.
---

# Karpathy Guidelines: Engineering Baseline

The behavioral baseline for every coding agent in Daniel's setup (Claude Code, Codex, Gemini CLI, OpenCode). Derived from Andrej Karpathy's observations on where LLMs fail at coding. This is the methodology layer: lighter than a skills framework, judgment-based, always on.

**Tradeoff:** these principles bias toward caution over speed on non-trivial work. For trivial tasks (a typo, an obvious one-liner) use judgment and just do it. This sits alongside the "direct execution by default" rule: execute clear requests immediately, but apply the caution below when work is ambiguous, non-trivial, or hard to reverse.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State assumptions explicitly. If uncertain, ask instead of guessing.
- If multiple interpretations exist, present them. Don't pick one silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what is confusing, and ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that was not requested.
- No error handling for impossible scenarios.
- If you write 200 lines and 50 would do, rewrite it.

The test: would a senior engineer call this overcomplicated? If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't improve adjacent code, comments, or formatting.
- Don't refactor things that are not broken.
- Match the existing style, even if you would do it differently.
- Notice unrelated dead code? Mention it, do not delete it.
- Remove the imports, variables, and functions YOUR change orphaned. Leave pre-existing dead code unless asked.

The test: every changed line traces directly to the request.

## 4. Goal-Driven Execution

**Define success criteria, then loop until verified.**

- "Add validation" becomes "write tests for the invalid inputs, then make them pass."
- "Fix the bug" becomes "write a test that reproduces it, then make it pass."
- "Refactor X" becomes "ensure tests pass before and after."

For multi-step work, state a short plan with a verification per step:

```
1. [step] -> verify: [check]
2. [step] -> verify: [check]
3. [step] -> verify: [check]
```

Strong criteria let you run independently. Weak criteria ("make it work") force constant clarification.

## Stack Standards (the verify step, tailored)

When the success criterion is "it builds and runs," verify against the stack:

- shadcn/ui for all UI, always. Next.js 16 uses `proxy.ts`, never `middleware.ts`.
- Typecheck while the dev server is up with `npx tsc --noEmit`. Never run `npm run build` while `npm run dev` is running; they share `.next/` and corrupt each other.
- Supabase keys use `sb_publishable_` / `sb_secret_`. Default Claude model `claude-sonnet-4-6`, default Gemini model `gemini-3`.
- Commits are Daniel's alone: no Co-Authored-By, no AI attribution, ever.

## Working signal

These guidelines are working when diffs contain only the requested changes, code is simple the first time, clarifying questions come before implementation rather than after mistakes, and PRs are clean with no drive-by refactoring.

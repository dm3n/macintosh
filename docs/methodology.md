# Engineering Methodology: Karpathy Guidelines

Macintosh uses one behavioral baseline across all four coding agents (Claude Code, Codex, Gemini CLI, OpenCode): the **Karpathy guidelines**, derived from Andrej Karpathy's observations on where LLMs fail at coding. It replaced a heavier skills framework (superpowers) with a lighter, judgment-based layer that is always on.

This is a methodology, not a skills engine. It does not script a workflow. It sets four principles that cut the common LLM coding failure modes, and it leaves the heavier process to the named macintosh skills (see [skills.md](skills.md)).

**Tradeoff:** the guidelines bias toward caution over speed on non-trivial work. For trivial tasks (a typo, an obvious one-liner) use judgment. This coexists with the "direct execution by default" rule: execute clear requests immediately, and apply the caution below when work is ambiguous, non-trivial, or hard to reverse.

## The Problems

From Karpathy's observations, LLMs tend to:

- make wrong assumptions and run with them without checking, instead of seeking clarification, surfacing inconsistencies, or presenting tradeoffs;
- overcomplicate code and APIs, bloat abstractions, and write 1000 lines where 100 would do;
- change or remove code and comments they do not fully understand, as side effects orthogonal to the task.

## The Four Principles

### 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs. State assumptions explicitly and ask when uncertain. Present multiple interpretations instead of picking one silently. Push back when a simpler approach exists. When something is unclear, stop, name it, and ask.

### 2. Simplicity First

Minimum code that solves the problem, nothing speculative. No unrequested features, abstractions, configurability, or error handling for impossible cases. If 200 lines could be 50, rewrite it. The test: would a senior engineer call this overcomplicated?

### 3. Surgical Changes

Touch only what you must, and clean up only your own mess. Don't improve, refactor, or reformat adjacent code. Match existing style. Mention unrelated dead code rather than deleting it. Remove only the imports, variables, and functions that your own change orphaned. Every changed line should trace directly to the request.

### 4. Goal-Driven Execution

Define success criteria, then loop until verified. Turn imperative tasks into verifiable goals: "fix the bug" becomes "write a test that reproduces it, then make it pass." For multi-step work, state a short plan with a verification per step. Strong criteria let an agent run independently; weak criteria ("make it work") force constant clarification.

## Tailored Verify Step (this stack)

When the success criterion is "it builds and runs," verify against the stack:

- shadcn/ui for all UI, always. Next.js 16 uses `proxy.ts`, never `middleware.ts`.
- Typecheck while the dev server is up with `npx tsc --noEmit`. Never run `npm run build` while `npm run dev` is running; they share `.next/` and corrupt each other.
- Supabase keys use `sb_publishable_` / `sb_secret_`. Default Claude model `claude-sonnet-4-6`, default Gemini model `gemini-3`.
- Commits are Daniel's alone: no Co-Authored-By, no AI attribution, ever.

## Where It Lives

| Surface | Form |
|---|---|
| Global Claude Code | `~/.claude/CLAUDE.md` (Engineering Methodology section) |
| Codex CLI | `~/.codex/AGENTS.md` (identical section) |
| Gemini CLI | `~/.gemini/GEMINI.md` (identical section) |
| OpenCode | `~/.config/opencode/AGENTS.md` (identical section) |
| Invokable skill | `~/.claude/skills/macintosh/karpathy.md` and `~/.agents/skills/macintosh/karpathy.md` |
| Repo source | `skills/karpathy.md` |

The same section is byte-identical in all four agent configs, so every agent shares one methodology.

## How to Know It Is Working

- Fewer unnecessary changes in diffs: only requested changes appear.
- Fewer rewrites from overcomplication: code is simple the first time.
- Clarifying questions come before implementation, not after mistakes.
- Clean, minimal PRs with no drive-by refactoring.

## Reference

Derived from [Andrej Karpathy's observations on LLM coding pitfalls](https://x.com/karpathy/status/2015883857489522876). Guideline packaging inspired by the [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) project, adapted and tailored to this setup.

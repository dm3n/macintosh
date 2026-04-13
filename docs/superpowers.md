# Superpowers

Macintosh uses a unified Superpowers standard across all coding agents.

Superpowers is our execution methodology layer: it enforces disciplined engineering workflows instead of ad-hoc prompting.

## What Superpowers Does

- forces design before implementation when scope is unclear
- converts approved designs into explicit implementation plans
- enforces test-first and verification-first execution
- standardizes review and branch completion behavior
- keeps multi-agent runs structured and auditable

## Core Workflow

Default sequence used by our coding agents:

1. **Brainstorming**
- clarify intent, constraints, and success criteria
- align on design before code changes

2. **Writing Plans**
- produce task-level implementation plan with file-level ownership
- include concrete validation steps

3. **Execution Mode**
- use subagent-driven development or inline plan execution
- keep changes scoped and reviewable

4. **Test-Driven Development**
- red/green/refactor pattern where applicable
- avoid speculative implementation

5. **Requesting Code Review**
- verify plan compliance and quality gates
- catch correctness/security/regression issues early

6. **Verification Before Completion**
- run checks before claiming success
- evidence over assertions

7. **Finishing Development Branch**
- pick merge/PR/cleanup path cleanly
- preserve branch hygiene

## Skill Categories We Rely On

- **Process and planning**: `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`
- **Quality and safety**: `test-driven-development`, `requesting-code-review`, `verification-before-completion`
- **Debugging**: `systematic-debugging`
- **Branch/worktree discipline**: `using-git-worktrees`, `finishing-a-development-branch`

## Installation Standard (Macintosh)

### Codex CLI
- repo location: `~/.codex/superpowers`
- skill link: `~/.agents/skills/superpowers -> ~/.codex/superpowers/skills`

### Claude Code
- plugin marketplace includes Superpowers at user scope

### Gemini CLI
- extension installed from the Superpowers source

### OpenCode
- global Superpowers plugin configured in `~/.config/opencode/opencode.json`

## Operational Rules

- Superpowers is mandatory across all four coding CLIs.
- Missing Superpowers is treated as environment drift.
- Update cadence is regular and explicit.

Update command baseline:

```bash
git -C ~/.codex/superpowers pull --ff-only
```

Then restart active CLIs.

## Verification Checklist

- each CLI can discover Superpowers skills
- workflow-triggering prompts invoke the correct skill path
- no CLI operates without the shared standards loaded

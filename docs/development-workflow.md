# Development Workflow

> Every feature starts with a natural language spec from Daniel and ends with a production deployment — no manual code review cycles, no context switching.

---

## The Agent Pipeline

```
Daniel (Architect)
    │
    │  "Build X that does Y"
    ▼
Claude Code — Architect Agent
    │  reads codebase, writes implementation plan
    │  breaks into tasks, assigns to Coder Agent
    ▼
Claude Code — Coder Agent
    │  implements on feature branch
    │  writes tests, follows existing patterns
    ▼
Claude Code — QA Agent
    │  launches real Chromium browser against dev server
    │  tests all affected user flows end-to-end
    │  writes regression tests for every bug found
    ▼
Pull Request (GitHub)
    │
    ▼
Claude Code — Reviewer Agent
    │  reads full diff
    │  checks: correctness, security, style, edge cases
    │  approves or requests changes with specific comments
    ▼
Merge to main
    │
    ▼
Vercel (auto-deploy)
    │
    ▼
Production
```

---

## Agent Definitions

All agent definitions live in `.claude/agents/` inside each project repo. Three agents are always present:

### Architect Agent (`architect-agent.md`)
**When:** At the start of every feature or system-level change.

Responsibilities:
- Read the relevant areas of the codebase before touching anything
- Write an implementation plan with ordered tasks
- Identify which files need to change and why
- Consider architectural trade-offs
- Spawn the Coder Agent with a precise brief

### Coder Agent (`coder-agent.md`)
**When:** During implementation.

Responsibilities:
- Follow the Architect's plan exactly
- Write code that matches the existing style and patterns in the repo
- Never introduce new dependencies without checking with Architect
- Open a PR when implementation is complete
- Include a clear PR description: what changed, why, how to test

### QA Agent (`qa-agent.md`)
**When:** After implementation, before opening the PR.

Responsibilities:
- Start the dev server and launch a real Chromium browser via Playwright
- Map every changed file to the user flows it affects
- Test all standard Airbank flows: auth, workbook, data room, flags, export
- Write a regression test for every bug found
- Produce a QA report: flows tested, bugs found, tests written

Standard flows tested every run:
- Login / session persistence
- Dashboard workbook list + create
- QoE workbook: cells, flags (create → comment → resolve), export
- Data room: upload, checklist, chat
- Settings: doc upload, SSE re-analyze stream

### Reviewer Agent (`code-reviewer.md`)
**When:** After QA passes, before merge.

Responsibilities:
- Read the full diff
- Check for: logic errors, security vulnerabilities, missing error handling, performance issues
- Verify the implementation matches the original spec
- Leave specific, actionable comments
- Approve only when all issues are resolved

### Security Agent (`security-agent.md`)
**When:** Before customer onboarding, investor demos, or any ship touching auth/upload/API/RLS.

Responsibilities:
- OWASP Top 10 audit across the full API surface
- STRIDE threat model on the three highest-risk surfaces: document upload pipeline, share tokens, AI chat
- `npm audit` for dependency CVEs
- Scan for secrets in client-side code, raw SQL, dangerouslySetInnerHTML
- Produce a severity-ranked findings report with concrete fixes

Run schedule:
- **Always:** before first paying customer, before investor demos with live data
- **Scoped:** after any new API endpoint, RLS policy change, or file upload change

---

## Branch Strategy

```
main ──────────────────────────────────────────── (production, protected)
  │
  ├── feature/qoe-working-capital-peg
  ├── feature/legal-dd-module
  ├── fix/cell-patch-validation
  └── chore/sync-vault-script
```

- `main` is always deployable. Every push to `main` triggers a Vercel production deploy.
- Feature branches are created per task from Linear issues.
- Branch names follow the pattern: `type/description` (feature, fix, chore, docs).
- No direct commits to `main` — everything goes through a PR.

---

## GitHub → Vercel → Production

```
Push to main
    │
    ▼
GitHub Actions (if configured)
    │  lint, type-check, build check
    ▼
Vercel Build
    │  next build
    │  ~1-2 minutes
    ▼
Preview URL generated (every PR)
    │
    ▼
Production deploy (on merge to main)
    │
    ▼
Slack #dev notification
```

**Environment variables** are managed in Vercel dashboard and `.env.local` locally. Never committed to git.

---

## Linear Integration

Every development task maps to a Linear issue:

1. Feature request or bug → Linear issue created (title + description)
2. Linear issue → branch name (e.g. `feature/qoe-flags-panel` from issue `ENG-42`)
3. PR description references Linear issue ID → auto-links in Linear
4. PR merge → Linear issue auto-closes

This keeps the entire backlog clean and traceable without manual overhead.

---

## PR Standards

Every PR must have:
- **Title**: `[type]: short description` (e.g. `feat: add working capital peg module`)
- **Summary**: what changed and why (3-5 bullets)
- **Test plan**: how to verify it works
- **Screenshots** (for UI changes)

The Reviewer Agent enforces this before approving.

---

## Local Development

```bash
# Airbank Platform
cd "/Users/dm3n/Airbank/Airbank Platform"
npm run dev          # → http://localhost:3000

# Airbank Website
cd "/Users/dm3n/Airbank/Airbank Website"
npm run dev          # → http://localhost:3001

# ROGI
cd "/Users/dm3n/Projects by Claude/rogi"
npm run dev -- --port 3002  # → http://localhost:3002
```

Terminal: **Warp** with Zsh. AI command suggestions enabled. Split panes for dev server + Claude Code side by side.

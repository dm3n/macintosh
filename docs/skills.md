# Macintosh Skills

A `karpathy` methodology baseline, three engineering disciplines (`debug`, `tdd`, `verify-done`), and 14 specialist Claude Code skills, installed globally at `~/.claude/skills/macintosh/`. Use them via the `Skill` tool or `/skill-name` slash command inside Claude Code.

The [Karpathy guidelines](methodology.md) are the always-on engineering baseline (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution). The disciplines are the few high-value workflows kept from the old superpowers set: systematic debugging, test-first, and evidence-before-done. The specialist skills sit on top and fill the gaps: product thinking, design, live testing, security, and release operations.

---

## The Sprint — Full Workflow

Skills run in the order a sprint runs:

**Think → Plan → Build → Review → Test → Ship → Reflect**

```
/product-review       ← challenge the idea before writing code
/autoplan             ← feature description → complete implementation plan
  [build against goal-driven success criteria, one verify step per task]
/design-shotgun       ← explore UI variants before committing
/plan-design-review   ← check design spec before building
  [implement]
/design-review        ← audit and fix UI after implementation
/qa                   ← live browser testing on staging
/devex-review         ← test the user's actual experience
/cso                  ← security audit before shipping
/careful              ← gate for any risky production operation
/canary               ← staged rollout plan for high-risk features
/document-release     ← generate release notes
/retro                ← weekly: what shipped, what didn't, what's next
```

---

## Skill Reference

### `/karpathy`
**Role:** Engineering baseline
**File:** `skills/karpathy.md`

The always-on methodology layer for every coding agent: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution. Tailored to the stack (shadcn/ui, `npx tsc --noEmit` while dev runs, `proxy.ts` not `middleware.ts`). Not usually invoked by hand; it is the default behavior the other skills build on. Invoke explicitly for a refresher or to re-anchor a drifting session.

---

### `/debug`
**Role:** Engineering discipline
**File:** `skills/debug.md`

Systematic debugging: reproduce, isolate, root-cause, minimal fix, verify. Prevents symptom-patching and guess-and-check. Invoke on any bug, test failure, or unexpected behavior before proposing a fix.

---

### `/tdd`
**Role:** Engineering discipline
**File:** `skills/tdd.md`

Lean test-first for non-trivial logic: red, green, refactor. For bugs, write the reproducing test first. Skips trivial UI glue by design. Pairs with `/debug` and `/qa`.

---

### `/verify-done`
**Role:** Engineering discipline
**File:** `skills/verify-done.md`

Evidence before claiming done: run the check, show the output, then claim success. The cross-agent version of Claude Code's built-in `/verify` (works in Codex, Gemini, OpenCode too). Use before committing or opening a PR.

---

### `/product-review`
**Role:** Founder / YC Partner
**File:** `skills/product-review.md`

YC-style product interrogation. Six forcing questions that cut through feature requests to find the real pain. Challenges framing, narrows scope, generates implementation alternatives.

Run this before building anything non-trivial. If you can't answer the six questions, you're not ready to build.

Modes:
- Default: challenge and reframe
- `--mode reduce`: aggressively cut scope
- `--mode expand`: find what you're leaving on the table

---

### `/autoplan`
**Role:** Architect
**File:** `skills/autoplan.md`

Convert a feature description into a complete, ready-to-execute implementation plan. Reads the current codebase, identifies every file to touch, maps risks and dependencies, breaks work into discrete tasks.

Output goes to `docs/plans/YYYY-MM-DD-[feature]-plan.md`, structured as goal-driven steps (one verify check per step) so it can be executed and checked independently.

Use when: you know what you want to build and don't need product interrogation.

---

### `/design-review`
**Role:** Senior Designer
**File:** `skills/design-review.md`

Audits UI code across six dimensions: shadcn/ui compliance, Tailwind v4 patterns, typography, layout/spacing, fintech aesthetic, accessibility, and mobile. Finds and fixes issues inline.

**shadcn/ui is the hard rule.** Every input, button, select, dialog, card, and tab must be a shadcn component. Raw HTML form elements are bugs.

AI slop detection included: generic placeholder text, unclear button labels, inconsistent icons, and inline `style={{}}` are all automatic failures.

Run after implementing any UI feature. Run before every PR.

---

### `/plan-design-review`
**Role:** Design Reviewer
**File:** `skills/plan-design-review.md`

Spec-level design audit before implementation begins. Checks shadcn/ui component feasibility, component reuse opportunities, design system consistency, edge case coverage, and complexity estimation.

Run this on any design spec that touches the UI. A 10-minute review here prevents hours of rework.

---

### `/design-shotgun`
**Role:** Design Explorer
**File:** `skills/design-shotgun.md`

Generate 4–6 UI variants for a component or screen as real, working React code using shadcn/ui + Tailwind v4. Each variant is droppable into the codebase.

Varies across: layout, density, visual weight, information hierarchy. Taste memory learns what you like over sessions (Mercury/Linear/Stripe aesthetic — neutral, high-contrast, data-first).

Run before committing to any significant UI shape. Explore > commit.

---

### `/qa`
**Role:** QA Lead
**File:** `skills/qa.md`

Live browser testing against a URL or local port. Navigates key flows like a real user, checks for visual regressions, console errors, form completeness, and shadcn/ui compliance.

Stack-specific checks: Supabase session cookies, SSE stream health, file upload flows, mobile at 375px.

Run before every feature ship. Use against `http://localhost:3000`, `http://localhost:3004`, or a staging URL.

---

### `/devex-review`
**Role:** DX Auditor
**File:** `skills/devex-review.md`

Tests the actual user experience of your key flows by walking through them as a first-time user. Measures time-to-core-action, records friction points with severity, and fixes or files what's found.

Three audit modes:
- `borrower` — portal invite link → first document uploaded (target: < 3 minutes)
- `apply` — application link → complete submission (target: < 12 minutes)
- `dev` — repo clone → first working service (target: < 10 minutes)

---

### `/cso`
**Role:** Chief Security Officer
**File:** `skills/cso.md`

OWASP Top 10 + STRIDE threat model, tuned for Airbank's fintech context: PII, mortgage data, Supabase auth and RLS, document uploads, API routes.

Outputs findings in Critical / High / Medium / Low tiers. Fixes Critical findings inline. Files High and Medium as Linear issues.

Run before any feature that touches auth, uploads, financial data, or API boundaries. Run quarterly as a full audit.

---

### `/benchmark`
**Role:** Performance Engineer
**File:** `skills/benchmark.md`

Measures: Lighthouse scores, Core Web Vitals (LCP/INP/CLS), API response times (median + p95), and Next.js bundle size.

Always captures before/after when used for optimization work. Targets: Performance ≥ 90, LCP < 2.5s, INP < 200ms, CLS < 0.1.

---

### `/retro`
**Role:** Engineering Lead
**File:** `skills/retro.md`

Weekly engineering retrospective across all active projects. Pulls git stats, categorizes what shipped, reviews against last week's goals, identifies patterns, and sets 3 priorities for next week.

Saves the report to `Brain/Raw/Company/` for PKB processing. Run every Monday morning.

---

### `/document-release`
**Role:** Release Engineer
**File:** `skills/document-release.md`

Turns git history into release notes in two formats:

- **Technical:** full detail, commit-level, for Linear and internal reference
- **Stakeholder:** plain language, outcome-focused, safe to share with LOI partners

Saves both to `Brain/Raw/Company/` for PKB archival.

---

### `/canary`
**Role:** Deployment Lead
**File:** `skills/canary.md`

Staged rollout planning for high-risk features. Defines canary population (internal → design partners → full rollout), success metrics per stage, rollback triggers, and copy-paste rollback commands.

Use for: auth changes, major data model changes, new third-party integrations, large rewrites.

---

### `/careful`
**Role:** Risk Officer
**File:** `skills/careful.md`

Explicit confirmation gate before destructive operations. Forces plain-language description of what's about to happen, lists failure modes, runs pre-flight checks, and waits for user confirmation before proceeding.

Invoked automatically before: DB migrations, RLS changes, auth modifications, production data scripts, force pushes.

---

### `/browse`
**Role:** Researcher
**File:** `skills/browse.md`

Real browser fetch for pages that require JavaScript. Use for: shadcn/ui docs, Supabase docs, competitor UX research, changelog pages, Linear API docs.

Summarizes findings and optionally saves to `Brain/Raw/Research/`.

---

## Relationship to the Methodology Baseline

The `karpathy` guidelines are the always-on baseline: how every change is made (cautious, simple, surgical, goal-driven). The specialist skills are the named workflows you reach for at specific points in a sprint. The baseline governs behavior; the specialists govern process.

| Baseline (`karpathy`) | Specialist skills |
|---|---|
| Think Before Coding | `product-review`, `plan-design-review` |
| Simplicity First | `design-review`, `design-shotgun` |
| Surgical Changes | `careful` (gates the risky ones) |
| Goal-Driven Execution | `autoplan`, `qa`, `cso`, `benchmark` |

When in doubt: the baseline is always on; reach for a specialist skill at its moment in the sprint.

---

## Installation

Skills are installed automatically by `scripts/bootstrap.sh` and `scripts/install.sh`.

To reinstall or update manually:

```bash
bash ~/lab/homelab-macintosh/scripts/install-skills.sh
```

Then restart Claude Code.

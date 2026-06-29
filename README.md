# Macintosh

Macintosh is my personal AI engineering OS: the complete, end-to-end system I use to build Airbank. It spans a local multi-agent coding workstation, a self-maintaining knowledge brain, a 14-skill Claude Code team, a self-hosted personal cloud running approval-gated automation agents, and a Linux AI/security node. This README is the full technical overview of how those pieces fit together.

Think of it as a custom, founder-grade version of [gstack](https://github.com/garrytan/gstack): tuned to my exact stack (Next.js 16, React 19, Supabase, GCP, shadcn/ui), wired to a Proxmox homelab, and anchored by a persistent knowledge base that compounds across every session and every model.

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

---

## Contents

1. [System Architecture](#system-architecture)
2. [Layer 1: Local Operator Workstation](#layer-1-local-operator-workstation)
3. [Layer 2: Knowledge Brain (Self-Maintaining PKB)](#layer-2-knowledge-brain-self-maintaining-pkb)
4. [Layer 3: The Coding Pipeline and Skills](#layer-3-the-coding-pipeline-and-skills)
5. [Layer 4: Personal Cloud and Agent Hub](#layer-4-personal-cloud-and-agent-hub)
6. [Layer 5: Approval and Control](#layer-5-approval-and-control)
7. [Kali AI and Security Node](#kali-ai-and-security-node)
8. [Tech Stack](#tech-stack)
9. [Install and Bootstrap](#install-and-bootstrap)
10. [Repository Structure](#repository-structure)
11. [Engineering Standards](#engineering-standards)
12. [Documentation Index](#documentation-index)

---

## System Architecture

Macintosh is organised as five layers, each with a clear owner and boundary. Work originates locally, draws on compiled knowledge, and any action that touches the outside world passes through a human approval gate before delivery.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  LAYER 1  LOCAL OPERATOR WORKSTATION (Mac)                                 │
│    Superset (coding) + Warp (general shell)                                │
│    4 aligned CLI agents: Claude Code · Codex · Gemini CLI · OpenCode       │
│    superpowers baseline + 14 macintosh skills                             │
│                                                                            │
│  LAYER 2  KNOWLEDGE BRAIN  (Obsidian vault, iCloud-synced)                 │
│    LLM-WIKI: Raw/ (sources) -> compile -> Wiki/ (pages + index + log)      │
│    primitives: ingest · query · lint        Memory/ loaded per session     │
│                                                                            │
│  LAYER 3  CODING PIPELINE                                                  │
│    Think -> Plan -> Build -> Review -> Test -> Ship -> Reflect             │
│    superpowers (discipline) + macintosh skills (product/design/QA/sec)     │
└───────────────────────────────┬──────────────────────────────────────────┘
                                 │ Tailscale mesh
┌───────────────────────────────┴──────────────────────────────────────────┐
│  LAYER 4  PERSONAL CLOUD (Proxmox + Casa)                                  │
│    Agent Hub (Docker): orchestrator · mcp-gateway · approval · executor    │
│    6 domain agents: code · email · calendar · linear · slack · todo        │
│    state: Postgres + Redis        Kali VM: AI repository + security node    │
│                                                                            │
│  LAYER 5  APPROVAL AND CONTROL                                             │
│    agents draft pending_actions -> Linear approval -> executor delivers     │
│    every external write is gated; full audit trail in Postgres             │
└──────────────────────────────────────────────────────────────────────────┘
```

| Layer | Function | Owner | Primary docs |
|---|---|---|---|
| Local Workstation | Turns scoped work into tested, deployable output | Operator + CLI agents | [dev-environment](docs/dev-environment.md), [local-development-system](docs/local-development-system.md) |
| Knowledge Brain | Compiles raw input into reusable long-term memory | The model (curated by human) | [knowledge-brain](docs/knowledge-brain.md) |
| Coding Pipeline | Engineering discipline + specialist review | superpowers + skills | [development-workflow](docs/development-workflow.md), [skills](docs/skills.md), [superpowers](docs/superpowers.md) |
| Personal Cloud | Runs infrastructure and automation workloads | Homelab | [homelab-architecture](docs/homelab-architecture.md), [personal-cloud-cluster](docs/personal-cloud-cluster.md) |
| Approval and Control | Enforces human review before external delivery | Linear gate | [approval-flow](docs/approval-flow.md) |

![PKB Graph View](assets/screenshots/pkb-graph-view-2026-04-13.png)

---

## Layer 1: Local Operator Workstation

The Mac is the command center for code, context, and operator control. It owns implementation, debugging, documentation, and context synthesis. It does not own long-running infrastructure execution; that belongs to the personal cloud.

**Terminals.** Superset is the primary coding surface (implementation-first, agent-driven). A general shell handles everyday terminal workflows.

**Four aligned CLI agents.** Each runs the same context (Brain vault, project paths, engineering standards) through its own config file, so any agent can pick up where another left off.

| Agent | Config | Notes |
|---|---|---|
| Claude Code (primary) | `~/.claude/CLAUDE.md` + auto-memory at `~/.claude/projects/-Users-dm3n/memory/MEMORY.md` | Default model `claude-sonnet-4-6` |
| Codex CLI | `~/.codex/config.toml` + `~/.codex/AGENTS.md` | |
| Gemini CLI | `~/.gemini/GEMINI.md` | Default model `gemini-3` |
| OpenCode | `~/.config/opencode/AGENTS.md` | Also runs on the Kali node |

**superpowers** is a mandatory baseline on all four agents (brainstorming, TDD, debugging, code review, shipping discipline). Missing superpowers is treated as environment drift. See [docs/superpowers.md](docs/superpowers.md).

---

## Layer 2: Knowledge Brain (Self-Maintaining PKB)

The Brain is a personal implementation of Karpathy's **LLM-WIKI.md** architecture: a knowledge base the model maintains for itself. Knowledge is compiled once at ingest, not re-derived on every query (the RAG model). The synthesis cost is paid once, the wiki compounds with each new source, and queries read an already-compiled artifact. Full detail in [docs/knowledge-brain.md](docs/knowledge-brain.md).

**Strict role separation.** The human curates and directs (selects sources, sets direction, oversees synthesis). The model writes, cross-references, and reconciles. This is enforced by three layers, each with a single owner:

| Layer | Path | Owner |
|---|---|---|
| 1. Raw sources (immutable) | `Brain/Raw/` | Human |
| 2. Schema and rules | `Brain/System/PKB/schema.md` + `Brain/CLAUDE.md` | Co-authored |
| 3. Wiki (generated) | `Brain/Wiki/` | Model |

**Three operational primitives** cover all routine interaction. The engine scripts are vendored in this repo at [`scripts/pkb/`](scripts/pkb/) and installed to `~/.claude/scripts/` by `scripts/install-pkb.sh`.

| Primitive | Command | Effect |
|---|---|---|
| **Ingest** | `pkb-process.py` | Compile a `Raw/` source into summary + entity/concept pages, rebuild `index.md`, append to `log.md` |
| **Query** | `pkb-query.py "question"` | Read `index.md` first, synthesise a cited answer, optionally file it to `Wiki/Compiled/` |
| **Lint** | `pkb-lint.py` | Health check: orphans, broken links, stale claims, optional `--deep` contradiction scan |

**Two model-owned navigation files** make the wiki self-describing and remove the need for vector search at this scale:

- `Wiki/index.md`: auto-generated catalog of every page with a one-line summary, by category. Read first on every query.
- `Wiki/log.md`: append-only operations log; entries are `## [YYYY-MM-DD] op | title`, greppable with standard unix tools.

The nightly brain-sync (02:00) runs ingest and lint unattended, so new drops compile into the wiki and the wiki's health is reported every day. A second vault mirrors the Airbank codebase as a linked dependency graph, re-synced every 10 minutes.

---

## Layer 3: The Coding Pipeline and Skills

Development follows a single methodology across all agents: Think, Plan, Build, Review, Test, Ship, Reflect. superpowers supplies the core discipline; 14 macintosh skills fill the specialist gaps. All design skills enforce shadcn/ui. Skills install to `~/.claude/skills/macintosh/` via `scripts/install-skills.sh`.

| Skill | Role | What it does |
|---|---|---|
| `/product-review` | Founder / YC Partner | Six forcing questions before you build. Challenges framing, finds the real pain. |
| `/autoplan` | Architect | Feature description to complete implementation plan, files identified, risks noted. |
| `/design-review` | Senior Designer | Audits UI for shadcn/ui + Tailwind v4, fintech aesthetic, accessibility, mobile. |
| `/plan-design-review` | Design Reviewer | Spec-level design audit before implementation. |
| `/design-shotgun` | Design Explorer | Generates 4 to 6 UI variants as real shadcn/ui code, iterates to a winner. |
| `/qa` | QA Lead | Opens a real browser, navigates flows like a user, finds bugs CI misses. |
| `/devex-review` | DX Auditor | Times borrower portal, apply wizard, and dev setup; finds friction. |
| `/cso` | Chief Security Officer | OWASP Top 10 + STRIDE, tuned for fintech (PII, mortgage data, Supabase auth, uploads). |
| `/benchmark` | Performance Engineer | Lighthouse, Core Web Vitals, API timings, bundle size, with before/after. |
| `/retro` | Engineering Lead | Weekly retro across projects: commits, lines, features, next priorities. |
| `/document-release` | Release Engineer | Git log to release notes in technical (Linear) and stakeholder formats. |
| `/canary` | Deployment Lead | Staged rollout plan with gate criteria and rollback commands. |
| `/careful` | Risk Officer | Confirmation gate before destructive operations. |
| `/browse` | Researcher | Real browser fetch for JS-rendered docs or any URL WebFetch cannot handle. |

Full reference: [docs/skills.md](docs/skills.md).

![Superset Coding Workspace](assets/screenshots/superset-coding-workspace-2026-04-13.png)

---

## Layer 4: Personal Cloud and Agent Hub

The personal cloud is a Proxmox-based private compute pool (managed with Casa) that runs always-available workloads. On top of it runs the **Agent Hub**: a Docker stack of core services and six domain agents that monitor my tools and draft work. The services are a Node.js monorepo under [`services/`](services/) (Express, ioredis, pg, node-cron, pino, zod).

### Core services

| Service | Container | Port | Role |
|---|---|---|---|
| Orchestrator | `hub-orchestrator` | 3000 | Dispatcher and scheduler. Ingests cron/webhook/manual triggers, dispatches jobs over Redis, aggregates pending-action state, runs the morning report (`MORNING_REPORT_CRON`, default `0 7 * * *`). |
| MCP Gateway | `hub-mcp` | 3001 | Unified tool interface to GitHub, Gmail, Google Calendar, Google Tasks, Linear, Slack, and read-only filesystem. Write actions are draft-only. |
| Approval Gateway | `hub-approval` | n/a | Bridges `pending_actions` to Linear and maps Linear decisions back to status transitions. |
| Executor | `hub-executor` | n/a | Consumes approved actions and delivers them idempotently with retry/backoff. Never delivers an unapproved action. |
| Postgres | `hub-db` | 5432 | State of record (`postgres:16-alpine`). |
| Redis | `hub-redis` | 6379 | Job dispatch queue and event bus (`redis:7-alpine`). |

### Domain agents

Each agent runs on its own cron schedule, monitors a surface, and emits `pending_actions`. None act directly.

| Agent | Container | Default schedule | Watches / drafts |
|---|---|---|---|
| Code | `hub-agent-code` | `0 */4 * * *` | Repos in `CODE_TARGET_REPOS`; drafts PR-ready changes with risk notes |
| Email | `hub-agent-email` | `*/30 * * * *` | Inbox; classifies and drafts replies |
| Calendar | `hub-agent-calendar` | `0 * * * *` | Schedule; proposes reschedules and event changes |
| Linear | `hub-agent-linear` | `0 */2 * * *` | Linear team; triage and sprint digests |
| Slack | `hub-agent-slack` | `0 * * * *` | Channels in `SLACK_CHANNELS`; summarises and drafts outbound |
| Todo | `hub-agent-todo` | `0 */2 * * *` | Tasks; surfaces overdue/high-risk items |

### State schema (Postgres)

`agents` (registry + last-run stats), `jobs` (execution records, JSONB context), `pending_actions` (the approval queue: `action_type`, `summary`, `full_output`, `payload`, `status`, approval ref, timestamps), `agent_memory` (per-agent KV state), `audit_log` (every lifecycle event), `morning_reports` (daily digests). Schema: [`homelab/database/schema.sql`](homelab/database/schema.sql).

### Data flow

```text
domain agent  ->  pending_actions (Postgres)  ->  Redis jobs:dispatch
                                                       │
                                            approval-gateway
                                          creates Linear approval issue
                                                       │
                                     human approves / rejects in Linear
                                                       │
                                  pending_actions.status = approved
                                                       │
                                                 executor
                                  delivers via mcp-gateway (GitHub/Gmail/...)
                                                       │
                                 delivered_at set · audit_log appended
```

Deploy to a Proxmox node with `homelab/scripts/deploy.sh <node-ip>` (rsync to `/opt/agenthub/homelab`, then `docker compose up -d --build`). Open debugging tunnels with `homelab/scripts/ssh-tunnel.sh <node-ip>` (Postgres on `localhost:5433`, Redis on `localhost:6380`).

![Proxmox Kali Install](assets/screenshots/proxmox-kali-install-2026-04-13.png)

---

## Layer 5: Approval and Control

Every external action is a pending action until a human approves it. Linear is the system of record for approvals.

- Agents and core services create rows in `pending_actions` (`status = pending`).
- The approval gateway opens a Linear issue (labels: `approval`, `<agent>`, `<action-type>`).
- A decision in Linear flips the status to `approved` or `rejected`.
- The executor delivers only approved actions, then records `delivered` or `failed`.
- Every transition is written to `audit_log` for full lifecycle transparency.

Action types: `github_pr`, `send_email`, `create_event`, `update_event`, `create_task`, `update_task`, `draft_note`. Detail in [docs/approval-flow.md](docs/approval-flow.md).

---

## Kali AI and Security Node

Kali is a first-class Linux VM on the Proxmox cluster: the AI repository and cybersecurity node. Operator experience is a single command from any terminal over Tailscale:

```bash
ssh kali
```

It runs OpenCode against local Ollama models, with the heavy inference optionally offloaded to a GCP GPU VM (`ollama-gpu-1`, A100 40GB, project `nodebase-473513`, served at `http://35.239.94.39:11434/v1`). Lifecycle is controlled by `homelab/scripts/gcp-model-host.sh {start|stop|status}`. OpenCode sessions on Kali sync into the Brain at `Raw/Conversations/Kali OpenCode/` via `homelab/scripts/sync-kali-opencode-to-brain.sh`, so Linux-side work also compounds into the knowledge base. References: [docs/kali-ai-repository-node.md](docs/kali-ai-repository-node.md), [docs/kali-gcp-model-serving.md](docs/kali-gcp-model-serving.md).

![Kali SSH Access](assets/screenshots/kali-ssh-access-2026-04-13.png)

---

## Tech Stack

| Domain | Tools |
|---|---|
| AI and intelligence | Claude Code (primary), Claude.ai (strategy/writing), Gemini 3 (in-product), Vertex AI, Perplexity (research), local Ollama on Kali |
| Development | Superset, GitHub, Vercel, Linear |
| Standard app stack | Next.js 16, React 19, TypeScript, Tailwind v4, shadcn/ui (no exceptions) |
| Knowledge | Obsidian (Brain vault, iCloud-synced), Notion (company KB), Apple Notes (capture) |
| Communication | Slack (real-time), Linear (dev), Notion (async) |
| Infrastructure | GCP, Supabase (Postgres, RLS, auth, storage), Proxmox, Casa, Docker, Tailscale, Kali |
| Automation runtime | Node.js services (Express, ioredis, pg, node-cron, pino, zod, Resend) |

Full catalogue: [docs/tech-stack.md](docs/tech-stack.md).

---

## Install and Bootstrap

One-command install (clone or update, then bootstrap):

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

Manual:

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
cd ~/lab/homelab-macintosh
./scripts/bootstrap.sh        # validates repo, installs skills, installs PKB engine
make validate                 # repository consistency checks
```

`bootstrap.sh` copies `homelab/.env.example` to `homelab/.env`, installs the 14 skills to `~/.claude/skills/macintosh/`, and installs the PKB engine to `~/.claude/scripts/`. Restart Claude Code afterward so the skills load.

Bring up the homelab stack on a node:

```bash
cd homelab
cp -n .env.example .env        # fill credentials
docker compose up -d --build
docker compose ps
```

Make targets: `make install`, `make bootstrap`, `make validate`, `make homelab-up`, `make homelab-down`, `make homelab-logs`.

---

## Repository Structure

```text
.
├── assets/                         # readme/doc visuals + screenshots
├── docs/                           # full system documentation (see index below)
├── skills/                         # 14 macintosh Claude Code skills (source)
├── scripts/
│   ├── install.sh                  # one-command install/update
│   ├── bootstrap.sh                # local bootstrap (validate + skills + pkb)
│   ├── install-skills.sh           # installs skills to ~/.claude/skills/macintosh/
│   ├── install-pkb.sh              # installs PKB engine to ~/.claude/scripts/
│   ├── validate-repo.sh            # repo consistency checks
│   ├── scrub-commits.sh            # history utility
│   └── pkb/                        # PKB / LLM-WIKI engine (vendored source)
│       ├── pkb_common.py           #   index.md + log.md helpers
│       ├── pkb-process.py          #   ingest primitive
│       ├── pkb-query.py            #   query primitive
│       └── pkb-lint.py             #   lint primitive
├── homelab/
│   ├── docker-compose.yml          # Agent Hub runtime stack
│   ├── .env.example                # required env keys
│   ├── database/schema.sql         # state/approval/audit schema
│   └── scripts/                    # deploy, tunnel, proxmox, gcp, kali-sync
└── services/                       # Node.js monorepo
    ├── orchestrator/  mcp-gateway/  approval-gateway/  executor/
    ├── agents/{code,email,calendar,linear,slack,todo}/
    └── lib/                        # logger, http, db, redis factories
```

---

## Engineering Standards

- Use `shadcn/ui` for all UI work, every project, no exceptions.
- Next.js 16 uses `proxy.ts`, not `middleware.ts`.
- Supabase key format: `sb_publishable_` / `sb_secret_`.
- Default Gemini model: `gemini-3`. Default Claude model: `claude-sonnet-4-6`.
- Agents draft actions; they never execute external writes directly. Approval happens in Linear; the executor delivers only after approval.
- Secrets stay in `.env` and are never committed.

---

## Documentation Index

**System overview**
- [docs/system-birdseye.md](docs/system-birdseye.md)
- [docs/operator-workflows.md](docs/operator-workflows.md)

**Local development and agents**
- [docs/dev-environment.md](docs/dev-environment.md)
- [docs/local-development-system.md](docs/local-development-system.md)
- [docs/development-workflow.md](docs/development-workflow.md)
- [docs/agents.md](docs/agents.md)
- [docs/superpowers.md](docs/superpowers.md)
- [docs/skills.md](docs/skills.md)

**Knowledge brain**
- [docs/knowledge-brain.md](docs/knowledge-brain.md)

**Infrastructure and execution**
- [docs/homelab-architecture.md](docs/homelab-architecture.md)
- [docs/personal-cloud-cluster.md](docs/personal-cloud-cluster.md)
- [docs/kali-ai-repository-node.md](docs/kali-ai-repository-node.md)
- [docs/kali-gcp-model-serving.md](docs/kali-gcp-model-serving.md)
- [docs/approval-flow.md](docs/approval-flow.md)
- [docs/install.md](docs/install.md)
- [docs/setup.md](docs/setup.md)

**Context**
- [docs/tech-stack.md](docs/tech-stack.md)
- [docs/team-communication.md](docs/team-communication.md)
- [docs/repository-roadmap.md](docs/repository-roadmap.md)

---

## Related

This engineering OS is the infrastructure behind the work catalogued in my **[AI Systems Portfolio](https://github.com/dm3n/portfolio)**: production AI platforms, the Symphony autonomous dev runner, and frontier-model reasoning research.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

## Maintainer

Daniel Edgar, <daniel@nodebase.ca>

<sub>Last updated: June 2026</sub>

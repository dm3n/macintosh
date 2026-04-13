# Macintosh

> Personal AI Operating System for lifelong compounding of code, knowledge, and execution.

Macintosh is a unified system for how Daniel builds Airbank and runs an AI-native company:
- Agent-driven development workflow
- Persistent Personal Knowledge Brain (PKB)
- Self-hosted homelab runtime with approval gating
- Team coordination stack (Slack, Linear, Notion)
- Reproducible environment and operating standards

If this repo is the front door, the goal is simple: clear architecture, truthful scope, and an install path that actually works.

## Why Macintosh Exists

Most "AI workflows" break over time because context fragments across chats, docs, repos, and tools.
Macintosh solves this by treating the system as one operating model:
- build software faster,
- preserve institutional memory forever,
- automate safely with explicit approvals,
- keep all layers observable and auditable.

## What The System Actually Does

At runtime, Macintosh coordinates five connected layers:

1. **Build Layer**: specs become shipped code through a structured agent loop.
2. **Knowledge Layer**: raw information is continuously compiled into reusable intelligence.
3. **Execution Layer**: homelab services run orchestrator + agents + queues.
4. **Safety Layer**: every write action is drafted first, then approved.
5. **Coordination Layer**: team signals from Slack/Linear/Notion feed back into the loop.

## System Overview (Detailed)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                           1) BUILD LAYER                                   │
│                                                                              │
│  Product spec -> Plan -> Implement -> QA -> Review -> PR -> Deploy         │
│  Output: tested code, tracked changes, deployment events                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         2) KNOWLEDGE LAYER (PKB)                           │
│                                                                              │
│  Raw Sources -> PKB Processing -> Structured Wiki -> Query -> Reuse         │
│  Output: persistent memory for future sessions and decisions                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        3) EXECUTION LAYER (HOMELAB)                        │
│                                                                              │
│  Orchestrator + Agents + Queue + DB + Redis + MCP Gateway                  │
│  Output: pending actions, reports, drafts, and automation candidates        │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         4) SAFETY + APPROVAL LAYER                         │
│                                                                              │
│  Pending action -> Telegram approve/reject -> Executor delivers             │
│  Output: controlled automation with complete audit trail                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        5) COORDINATION + FEEDBACK                          │
│                                                                              │
│  Slack / Linear / Notion signals -> prioritize -> feed Build + PKB          │
│  Output: closed-loop operating system for company execution                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Personal Knowledge Brain (PKB)

The PKB is the long-term memory and context engine behind the entire system.

<p align="center">
  <img src="assets/brain-graph.png" alt="Obsidian PKB graph view" width="85%" />
</p>

**PKB pipeline:**
- `Brain/Raw/*` receives articles, meetings, notes, and research
- `pkb-process.py` compiles raw input into structured outputs
- `Brain/Wiki/*` stores entities, concepts, SOPs, and summaries
- `pkb-query.py` answers questions across the full memory graph
- high-value outputs are written back for continuous compounding

This converts one-off conversations into a reusable operating asset.

## UX / Operator Experience

Macintosh is intentionally designed as a multi-surface operator UX:

| Surface | Primary Job | Why It Matters |
|---|---|---|
| **Obsidian Graph + Wiki** | Long-horizon memory and retrieval | Prevents context loss across years of work |
| **Terminal (Superset + Zsh)** | Build, inspect, deploy, validate | Fastest control surface for engineering loops |
| **Telegram Approval UI** | Approve/reject pending actions | Keeps automation safe without slowing momentum |
| **GitHub** | Code review + merge history | Source-of-truth for implementation quality |
| **Slack / Linear / Notion** | Team coordination and intent capture | Connects execution to real company priorities |

Design principle: each surface has one clear role, and all surfaces feed the same shared operating model.

## One-Command Install

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

Defaults:
- repository: `https://github.com/dm3n/macintosh.git`
- install directory: `~/lab/homelab-macintosh`

Custom install:

```bash
MACINTOSH_DIR="$HOME/custom/macintosh" \
MACINTOSH_REPO="https://github.com/dm3n/macintosh.git" \
bash -c "$(curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh)"
```

## Quick Start

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
cd ~/lab/homelab-macintosh
./scripts/bootstrap.sh
```

Bootstrap does three things:
- verifies core prerequisites
- creates `homelab/.env` from template if missing
- runs repository validation checks

## Homelab Runtime

```bash
cd homelab
cp -n .env.example .env
# add secrets
docker compose up -d
```

Current runtime status:
- compose stack is defined and buildable
- scaffold services are runnable for all core components
- integration handlers are intentionally incremental

## Repository Layout

```text
.
├── assets/                         # readme/docs images
├── docs/                           # architecture, setup, ops, roadmap
├── homelab/
│   ├── docker-compose.yml          # runtime stack definition
│   ├── .env.example                # required configuration keys
│   ├── database/schema.sql         # queue + audit + report schema
│   └── scripts/                    # deploy and tunnel helpers
├── scripts/
│   ├── install.sh                  # one-command install/update
│   ├── bootstrap.sh                # local bootstrap
│   ├── validate-repo.sh            # repo quality guardrail
│   └── scrub-commits.sh            # optional history scrub utility
└── services/
    ├── orchestrator/               # dispatch + report service
    ├── mcp-gateway/                # integration tool gateway
    ├── telegram-bot/               # approval interface service
    ├── executor/                   # approved action delivery service
    ├── agents/                     # code/email/calendar/linear/slack/todo
    └── lib/                        # shared runtime helpers
```

## Truthful Scope

Implemented now:
- architecture + operating documentation
- install/bootstrap/validation pipeline
- homelab compose + schema + deploy scripts
- runnable Node service scaffolds for all compose services

In progress:
- deep external integration handlers (GitHub/Gmail/Calendar/Linear/Slack)
- production-grade decision policies per agent
- hardened E2E integration test coverage

## Standards

Non-negotiable project standards:
- UI work uses `shadcn/ui`
- Next.js 16 uses `proxy.ts` (not `middleware.ts`)
- Supabase keys use `sb_publishable_` / `sb_secret_`
- default Gemini family is **Gemini 3**
- default Claude model is `claude-sonnet-4-6`

## Security Model

Macintosh defaults to safe automation:
- draft-first, execute-on-approval
- explicit user approval for all external writes
- audit trail across action lifecycle (`pending -> approved/rejected -> delivered/failed`)
- private infra posture via Tailscale + SSH

## Documentation Map

- [docs/install.md](docs/install.md)
- [docs/setup.md](docs/setup.md)
- [docs/homelab-architecture.md](docs/homelab-architecture.md)
- [docs/approval-flow.md](docs/approval-flow.md)
- [docs/development-workflow.md](docs/development-workflow.md)
- [docs/dev-environment.md](docs/dev-environment.md)
- [docs/knowledge-brain.md](docs/knowledge-brain.md)
- [docs/tech-stack.md](docs/tech-stack.md)
- [docs/team-communication.md](docs/team-communication.md)
- [docs/airbank-stack.md](docs/airbank-stack.md)
- [docs/repository-roadmap.md](docs/repository-roadmap.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

## Maintainer

Daniel Edgar — <daniel@nodebase.ca>

# Macintosh

Personal AI operating system for building software, compounding knowledge, and running approval-safe automation.

Macintosh is the operating model behind Airbank. It combines product development, persistent memory, automation runtime, and team coordination into one coherent system.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

## What This Repo Covers

- reproducible install/bootstrap/validation
- homelab runtime stack (compose + schema + service scaffolds)
- linear-based approval model for all agent actions
- persistent PKB architecture and workflows
- team/system docs as source of truth

## 5-Layer System

| Layer | What It Does | Deep-Dive Docs |
|---|---|---|
| **1. Build Layer** | Converts scoped work into reviewed, deployable changes | [docs/development-workflow.md](docs/development-workflow.md), [docs/dev-environment.md](docs/dev-environment.md) |
| **2. Knowledge Layer (PKB)** | Turns raw inputs into reusable long-term memory | [docs/knowledge-brain.md](docs/knowledge-brain.md) |
| **3. Execution Layer (Homelab)** | Runs orchestrator, agents, queues, and delivery services | [docs/homelab-architecture.md](docs/homelab-architecture.md), [docs/setup.md](docs/setup.md), [docs/install.md](docs/install.md) |
| **4. Approval Layer** | Enforces human approval in Linear before external writes | [docs/approval-flow.md](docs/approval-flow.md) |
| **5. Coordination Layer** | Aligns priorities and communication across tools | [docs/team-communication.md](docs/team-communication.md), [docs/agents.md](docs/agents.md) |

## System Flow

```text
Spec / Signal
  -> Build Layer creates or updates implementation
  -> Agents draft actions and findings
  -> Pending actions are synced to Linear approvals
  -> Approved actions are executed by Executor
  -> Outcomes are logged and fed into PKB
```

## PKB Visual

<p align="center">
  <img src="assets/brain-graph.png" alt="Macintosh PKB graph view" width="85%" />
</p>

The PKB is the memory backbone:
- ingest raw material from notes, sessions, research, and conversations
- compile into linked wiki entities/concepts/summaries/SOPs
- query across accumulated context
- feed validated output back into future sessions

## Runtime Architecture (Current)

- **Orchestrator**: schedules and dispatches jobs
- **MCP Gateway**: integration abstraction layer
- **Approval Gateway**: Linear approval synchronization
- **Executor**: executes only approved actions
- **Agents**: code, email, calendar, linear, slack, todo
- **State**: Postgres + Redis

## Quick Start

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
cd ~/lab/homelab-macintosh
./scripts/bootstrap.sh
```

Bring homelab up:

```bash
cd homelab
cp -n .env.example .env
# fill credentials
docker compose up -d --build
```

## Repository Layout

```text
.
├── assets/                         # images used in docs/readme
├── docs/                           # system documentation
├── homelab/
│   ├── docker-compose.yml          # runtime stack definition
│   ├── .env.example                # required env keys
│   ├── database/schema.sql         # queue/approval/audit schema
│   └── scripts/                    # deploy + tunnel scripts
├── scripts/
│   ├── install.sh                  # one-command install/update
│   ├── bootstrap.sh                # local bootstrap
│   ├── validate-repo.sh            # repo consistency checks
│   └── scrub-commits.sh            # optional history utility
└── services/
    ├── orchestrator/
    ├── mcp-gateway/
    ├── approval-gateway/
    ├── executor/
    ├── agents/
    └── lib/
```

## Standards

- `shadcn/ui` for UI work
- Next.js 16 uses `proxy.ts` (not `middleware.ts`)
- Supabase key format: `sb_publishable_` / `sb_secret_`
- default Gemini family: **Gemini 3**
- default Claude model: `claude-sonnet-4-6`

## Security Model

- agents draft, they do not execute external writes directly
- approval decision happens in Linear
- executor runs only approved actions
- full audit trail on action lifecycle
- secrets stay in `.env` and are never committed

## Docs Index

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

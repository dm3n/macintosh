# Macintosh

Personal AI operating system for building, running, and compounding an AI-native company over decades.

Macintosh combines five systems in one repo:
- Agentic software development pipeline
- Personal knowledge brain (PKB)
- Homelab agent runtime with human approvals
- Team operating stack (Slack, Linear, Notion)
- Reproducible local environment standards

This repository is designed as a long-horizon open-source system: explicit architecture, truthful scope, repeatable setup, and auditable operations.

## One-Command Install

```bash
curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh | bash
```

Default install directory: `~/lab/homelab-macintosh`

To customize:

```bash
MACINTOSH_DIR="$HOME/custom/macintosh" \
MACINTOSH_REPO="https://github.com/dm3n/macintosh.git" \
bash -c "$(curl -fsSL https://raw.githubusercontent.com/dm3n/macintosh/main/scripts/install.sh)"
```

## What You Get

- High-level architecture and operating docs in [`docs/`](docs)
- Homelab stack definition in [`homelab/docker-compose.yml`](homelab/docker-compose.yml)
- Postgres schema for approvals/audit flow in [`homelab/database/schema.sql`](homelab/database/schema.sql)
- Deployment helpers in [`homelab/scripts/`](homelab/scripts)
- Quality and consistency checks in [`scripts/validate-repo.sh`](scripts/validate-repo.sh)

## Current Scope (Truthful State)

Implemented in this repo today:
- System architecture and operating model documentation
- Homelab compose + env template + DB schema
- Operational scripts for deploy/tunnel/bootstrap/install/validation
- CI guardrails for repository quality
- Runnable Node.js service scaffolds for orchestrator, MCP gateway, Telegram approvals, executor, and all agents

Not yet implemented in this repo today:
- External integration handlers (GitHub/Gmail/Calendar/Linear/Slack) beyond scaffold endpoints
- Production-grade decision logic for each agent

`services/` now provides executable baseline services plus explicit contracts for each component.

## System Overview

### 1) Development Layer
Natural-language specs are converted into shipped features through an agent-assisted workflow:
`Spec -> Plan -> Code -> QA -> Review -> PR -> Deploy`

### 2) Knowledge Layer (PKB)
All high-value knowledge is continuously compiled into a persistent brain:
`Raw -> PKB process -> Wiki -> Query -> Reuse`

### 3) Homelab Layer
Self-hosted agent runtime on a 2-node Proxmox footprint with Docker services and approval gating.

### 4) Approval Layer
Every agent output is a pending action. Nothing executes without explicit human approval.

### 5) Coordination Layer
Slack + Linear + Notion connect communication, backlog, and knowledge capture.

## Repository Layout

```text
.
├── assets/                      # images used in docs
├── docs/                        # architecture + operating docs
├── homelab/
│   ├── docker-compose.yml       # stack definition
│   ├── .env.example             # required environment variables
│   ├── database/schema.sql      # approvals and audit schema
│   └── scripts/                 # deploy + tunnel utilities
├── scripts/
│   ├── install.sh               # one-command install/update
│   ├── bootstrap.sh             # local setup bootstrap
│   ├── validate-repo.sh         # repository quality checks
│   └── scrub-commits.sh         # optional history scrub utility
└── services/                    # service contracts and scaffolding
```

## Quick Start (Local)

```bash
git clone https://github.com/dm3n/macintosh.git ~/lab/homelab-macintosh
cd ~/lab/homelab-macintosh
./scripts/bootstrap.sh
```

Bootstrap will:
- verify required tools
- create `homelab/.env` from `homelab/.env.example` if missing
- run repository validation

## Homelab Start

```bash
cd homelab
cp -n .env.example .env
# fill secrets
docker compose up -d
```

This now starts all scaffold services successfully; integration-specific functionality is intentionally incremental.

## Docs Index

- [`docs/setup.md`](docs/setup.md): homelab setup sequence
- [`docs/install.md`](docs/install.md): local and remote installation paths
- [`docs/homelab-architecture.md`](docs/homelab-architecture.md): runtime design
- [`docs/approval-flow.md`](docs/approval-flow.md): safety and approval system
- [`docs/development-workflow.md`](docs/development-workflow.md): coding and release loop
- [`docs/dev-environment.md`](docs/dev-environment.md): local machine + agent configs
- [`docs/knowledge-brain.md`](docs/knowledge-brain.md): PKB system
- [`docs/tech-stack.md`](docs/tech-stack.md): full stack map
- [`docs/airbank-stack.md`](docs/airbank-stack.md): product architecture context
- [`docs/team-communication.md`](docs/team-communication.md): team operating flow
- [`docs/agents.md`](docs/agents.md): agent responsibilities
- [`docs/repository-roadmap.md`](docs/repository-roadmap.md): staged implementation roadmap

## Standards

Repository-wide standards:
- `shadcn/ui` for all UI work
- Next.js 16: use `proxy.ts`, not `middleware.ts`
- Supabase keys: `sb_publishable_` and `sb_secret_`
- Default Gemini family: Gemini 3
- Default Claude model: `claude-sonnet-4-6`

## Security Model

- Principle: draft-first, execute-on-approval
- Secrets never committed (`.env`, credentials files, service keys)
- Audit log for action lifecycle (`pending -> approved/rejected -> delivered/failed`)
- Private infrastructure via Tailscale + SSH

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. See [`LICENSE`](LICENSE).

## Maintainer

Daniel Edgar — <daniel@nodebase.ca>

Updated continuously as system architecture and infrastructure evolve.

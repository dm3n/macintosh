# Agents

This system has two distinct agent layers:

1. **Primary CLI coding agents** used for day-to-day software development.
2. **Homelab runtime domain agents** used for MCP-integrated automation workflows.

## 1) Primary CLI Coding Agents

These are the main development agents in the local environment.

| Agent | Role | Config |
|---|---|---|
| **Claude Code** | Primary implementation/review/deep context execution | `~/.claude/CLAUDE.md` |
| **Codex CLI** | High-speed coding and repo operations | `~/.codex/AGENTS.md` |
| **Gemini CLI** | Secondary coding path with Gemini models | `~/.gemini/GEMINI.md` |
| **OpenCode** | Alternate coding environment with plugin support | `~/.config/opencode/AGENTS.md` |

Shared requirements across all four:
- superpowers installed and active
- same core project/brain context
- same engineering standards

## 2) Homelab Runtime Agents (MCP/Software Domain)

These are not the primary coding CLIs. They are domain automation workers in the homelab runtime.

### Core Runtime Services

| Service | Responsibility |
|---|---|
| **Orchestrator** | Dispatches jobs and schedules runs |
| **MCP Gateway** | Provides integration/tool abstraction |
| **Approval Gateway** | Syncs pending actions with Linear approvals |
| **Executor** | Delivers approved actions |

### Domain Agents

| Agent | Domain |
|---|---|
| **Code Agent** | Repository scanning and draft code actions |
| **Email Agent** | Inbox analysis and draft replies |
| **Calendar Agent** | Conflict detection and draft event actions |
| **Linear Agent** | Backlog/sprint triage and updates |
| **Slack Agent** | Channel signal summaries and draft posts |
| **Todo Agent** | Task prioritization and draft task updates |

## Approval and Delivery Boundary

- Runtime/domain agents create pending actions.
- Approval happens in Linear.
- Executor performs delivery only for approved actions.

This keeps coding-agent workflows and runtime automation responsibilities cleanly separated.

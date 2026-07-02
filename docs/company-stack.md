# Company Software Stack

The complete stack used to run Finsider (finsider.ai) as an AI-native software company, and how the coding agents (Claude Code, Codex, Gemini CLI, OpenCode) reach each tool. Every tool is agent-accessible via MCP, CLI, or API — the agents operate the company across the whole stack, not just the codebase.

Credentials and per-machine wiring live in the private local setup, never in this repo.

## The Stack

| Tool | Runs | Agent access |
|---|---|---|
| **Claude / Codex / Gemini / OpenCode** | Engineering + operations brain | The agents themselves; shared context via global config files |
| **GitHub** | Code, CI/CD, open source | `gh` CLI |
| **Vercel** | Frontend hosting | Official MCP (`mcp.vercel.com`) + `vercel` CLI |
| **Microsoft Azure** | Backend hosting, OpenAI, Redis, storage, search | `az` CLI + service APIs |
| **Clerk** | Product authentication | Official MCP (`mcp.clerk.com/mcp`) + Backend API |
| **Railz** | Financial data ingestion & storage (the product's data backbone) | REST API v2, client-credentials flow |
| **Jira** | Support tickets, dev management, team todos | Atlassian MCP (`mcp.atlassian.com`) |
| **Notion** | Meetings, knowledge, brainstorming | Official MCP (`mcp.notion.com/mcp`) |
| **Slack** | Team communication | Connector MCP + bot-token API |
| **Google Drive** | Files | Workspace MCP |
| **Close** | Main sales CRM | Official MCP (`mcp.close.com/mcp`), API-key scoped |
| **Cal.com** | Scheduling | Official MCP (`mcp.cal.com/mcp`) wrapping API v2 |
| **Dripify** | Automated LinkedIn outreach | Webhooks-out → automation glue (no public API) |
| **Meow** | Spend cards, team spend, banking | Developer API (read/report only — agents never move money) |
| **Framer** | Marketing landers | Official Server API (CMS sync, publishing) |
| **Zapier** | Long-tail integration glue | Zapier MCP (`mcp.zapier.com`) |

## Principles

- **Everything agent-reachable.** If a tool can't be reached by MCP, CLI, or API, it gets a webhook bridge (Dripify) or is replaced. Agents store, move, and build with knowledge across the entire stack, not one silo.
- **Official MCPs first**, CLI second, raw API third, automation-glue (Zapier) last.
- **Hard money boundary.** Banking/spend access is read-and-reconcile only. No agent initiates transfers, payments, or card issuance — ever — without explicit per-action human approval.
- **Least-privilege writes.** CRM and auth tooling run on safe-write scopes by default; destructive scopes require explicit instruction.
- **Cross-stack loops** (e.g. meeting transcript → CRM lead → follow-up task → Slack ping) are built on the [loops](../skills/loops.md) architecture: deterministic single-trigger glue goes to Zapier; anything requiring judgment runs as a scheduled agent routine.

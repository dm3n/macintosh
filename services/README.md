# Services

This directory defines the runtime service boundaries for the Macintosh homelab system.

Current state:
- Interfaces and architecture are documented.
- Runnable scaffold implementations are committed for every compose-defined service.
- Production integration handlers are intentionally incremental.

Each service directory must at minimum contain:
- `README.md` with ownership, responsibilities, and API contract.

Planned services:
- `orchestrator`
- `mcp-gateway`
- `telegram-bot`
- `executor`
- `agents/code`
- `agents/email`
- `agents/calendar`
- `agents/todo`
- `agents/linear` (compose-defined)
- `agents/slack` (compose-defined)

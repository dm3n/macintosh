# Dev Environment

Local machine: macOS (Apple Silicon).
Single source of truth for the local dev pipeline, coding agents, and knowledge system.

---

## Terminal

- **Superset + Zsh** — coding-first terminal environment for implementation sessions
- **Warp** — general-purpose terminal for broader shell/ops workflows

---

## Coding Agents

Four AI coding agents are configured globally. They share aligned context (Brain vault, project paths, standards, and operating rules).

### Claude Code (primary)
- **CLI**: `claude`
- **Global config**: `~/.claude/CLAUDE.md`
- **Auto-memory**: `~/.claude/projects/-Users-dm3n/memory/MEMORY.md`
- **Hooks**: `~/.claude/settings.json`

### OpenCode
- **CLI**: `opencode`
- **Global config**: `~/.config/opencode/AGENTS.md`
- **Plugin base**: `@opencode-ai/plugin`

### Codex CLI
- **CLI**: `codex`
- **Global config**: `~/.codex/AGENTS.md`
- **Config**: `~/.codex/config.toml`

### Gemini CLI
- **CLI**: `gemini`
- **Global config**: `~/.gemini/GEMINI.md`
- **Default model**: `gemini-3`

### Global Superpowers Standard (All Agents)

Superpowers is required at user/global scope for every coding agent in this environment.

Full standard and workflow details:
- [docs/superpowers.md](superpowers.md)

Macintosh install baseline:
- Codex: `~/.codex/superpowers` + `~/.agents/skills/superpowers` symlink
- Claude Code: Superpowers plugin installed at user scope
- Gemini CLI: Superpowers extension installed
- OpenCode: Superpowers plugin configured globally

Update baseline:

```bash
git -C ~/.codex/superpowers pull --ff-only
```

---

## Shared Agent Context

All four CLI agent configs include:
- user/project context
- Brain vault references
- active project paths and ports
- engineering standards and model defaults
- homelab references

---

## Knowledge System — Brain Vault

Personal knowledge base in Obsidian, synced via iCloud.

**Vault path**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/`

### Directory Structure

```text
Brain/
├── Memory/
│   └── MEMORY.md
├── Raw/
│   ├── News/
│   ├── Blog/
│   ├── Personal/
│   ├── Company/
│   ├── Research/
│   ├── Conversations/
│   └── Inbox/
├── Wiki/
│   ├── Entities/
│   │   ├── People/
│   │   └── Companies/
│   ├── Concepts/
│   ├── Summaries/
│   ├── SOPs/
│   └── Compiled/
├── Claude Sessions/
├── Projects/
├── Apple Notes/
├── People/
└── System/
    └── PKB/
        └── schema.md
```

### PKB Scripts

| Command | What it does |
|---|---|
| `python3 ~/.claude/scripts/pkb-process.py` | Process all files in `Brain/Raw/` |
| `python3 ~/.claude/scripts/pkb-process.py --dry-run` | Preview processing |
| `python3 ~/.claude/scripts/pkb-process.py --file <path>` | Process one file |
| `python3 ~/.claude/scripts/pkb-query.py "question"` | Query across the Brain |
| `python3 ~/.claude/scripts/pkb-query.py "question" --save` | Query + save answer |
| `python3 ~/.claude/scripts/pkb-query.py --interactive` | Interactive mode |

---

## Active Projects

| Project | Path | Port | Stack |
|---|---|---|---|
| QoE Platform | `/Users/dm3n/Airbank/Airbank Platform` | 3000 | Next.js 16 + React 19 |
| Airbank Mortgage Platform | `/Users/dm3n/Airbank/Airbank Mortgage Platform` | 3004 | Next.js 16 |
| ROGI | `/Users/dm3n/Projects/rogi` | 3002 | Next.js 16 |

---

## Universal Engineering Rules

- Always use **shadcn/ui** for UI components
- Next.js 16: use `proxy.ts`, not `middleware.ts`
- Supabase key format: `sb_publishable_` / `sb_secret_`
- Default Gemini model: `gemini-3`
- Default Claude model: `claude-sonnet-4-6`
- Supabase project ID: `qlhdslbpgnctshcpiqfv`

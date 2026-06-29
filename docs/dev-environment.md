# Dev Environment

Local machine: macOS (Apple Silicon).
Single source of truth for the local dev pipeline, coding agents, and knowledge system.

---

## Terminal

- **Warp** — primary terminal for coding and implementation sessions
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

### Engineering Methodology Standard (All Agents)

The Karpathy guidelines are the engineering baseline for every coding agent in this environment: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.

Full standard and tailored verify step:
- [docs/methodology.md](methodology.md)

How it is deployed:
- The methodology lives as a byte-identical section in each agent's config: `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`, `~/.config/opencode/AGENTS.md`. Claude Code and Codex stay 100% aligned on it.
- Also available as an invokable skill at `~/.claude/skills/macintosh/karpathy.md` (Claude Code) and `~/.agents/skills/macintosh/karpathy.md` (Codex).

To re-sync the skill after editing `skills/karpathy.md`:

```bash
bash ~/lab/homelab-macintosh/scripts/install-skills.sh
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
| Finsider Mitch-fe | `~/finsider-platform/Mitch-fe` | 3000 | Next.js (Clerk auth) |
| Finsider Mitch-be | `~/finsider-platform/Mitch-be` | 1337 | Strapi / SQLite (Node 20) |

---

## Universal Engineering Rules

- Always use **shadcn/ui** for UI components
- Next.js 16: use `proxy.ts`, not `middleware.ts`
- Supabase key format: `sb_publishable_` / `sb_secret_`
- Default Gemini model: `gemini-3`
- Default Claude model: `claude-sonnet-4-6`
- Supabase project ID: `qlhdslbpgnctshcpiqfv`

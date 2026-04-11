# Dev Environment

Local machine: macOS (Apple Silicon).
Single source of truth for the local dev pipeline, coding agents, and knowledge system.

---

## Terminal

**Superset + Zsh** — primary terminal (replaced Warp).

---

## Coding Agents

Four AI coding agents installed and configured globally. All share the same context via their respective config files so every agent knows the full system — Brain vault, active projects, stack rules, homelab.

### Claude Code (primary)
- **CLI**: `claude`
- **Global config**: `~/.claude/CLAUDE.md`
- **Auto-memory**: `~/.claude/projects/-Users-dm3n/memory/MEMORY.md`
- **Skills**: `~/.claude/skills/` (commit, review-pr, simplify, schedule, loop, claude-api, etc.)
- **Hooks**: configured in `~/.claude/settings.json`
- **MCP servers**: Gmail, Google Calendar (via claude.ai MCP)

### OpenCode
- **CLI**: `opencode`
- **Global config**: `~/.config/opencode/AGENTS.md`
- **Plugin**: `@opencode-ai/plugin` v1.4.0
- **Built-in agents**: build, plan, explore, general, summary, title, compaction

### Codex CLI
- **CLI**: `codex`
- **Global config**: `~/.codex/AGENTS.md`
- **Config**: `~/.codex/config.toml`

### Gemini CLI
- **CLI**: `gemini`
- **Global config**: `~/.gemini/GEMINI.md`
- **Default model**: `gemini-2.0-flash-001`

---

## Shared Agent Context

All four configs contain the same foundational context:
- Who Daniel is and what Airbank is building
- Brain vault path + PKB pipeline commands
- Active projects, ports, local paths
- Universal rules (shadcn/ui, no middleware.ts, Supabase key format, model defaults)
- Homelab repo reference + approval model

---

## Knowledge System — Brain Vault

Personal knowledge base running in Obsidian, synced via iCloud.

**Vault path**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/`

### Directory Structure

```
Brain/
├── Memory/
│   └── MEMORY.md              # Master memory index (loaded by all agents at session start)
├── Raw/                       # Drop zone for source material
│   ├── News/                  # Articles, market intel, competitor news
│   ├── Blog/                  # Essays, posts, thought leadership
│   ├── Personal/              # Reflections, ideas, journal
│   ├── Company/               # Meeting notes, decisions, customer intel
│   ├── Research/              # Papers, reports, deep analysis
│   ├── Conversations/         # Transcripts, call notes, interviews
│   └── Inbox/                 # Unsorted drop zone
├── Wiki/
│   ├── Entities/
│   │   ├── People/            # Person pages (advisors, prospects, contacts)
│   │   └── Companies/         # Company pages
│   ├── Concepts/              # Compiled concept knowledge
│   ├── Summaries/             # Source summaries
│   ├── SOPs/                  # Standard operating procedures
│   └── Compiled/              # Cross-source Q&A answers
├── Claude Sessions/           # Past AI session summaries
├── Projects/                  # Project notes + git summaries
├── Apple Notes/               # Nightly export from Apple Notes
├── People/                    # Contact records (synced to iCloud Contacts)
└── System/
    └── PKB/
        └── schema.md          # Templates for all Wiki page types
```

### PKB Scripts

| Command | What it does |
|---|---|
| `python3 ~/.claude/scripts/pkb-process.py` | Process all files in `Brain/Raw/` |
| `python3 ~/.claude/scripts/pkb-process.py --dry-run` | Preview what would be processed |
| `python3 ~/.claude/scripts/pkb-process.py --file <path>` | Process a single file |
| `python3 ~/.claude/scripts/pkb-query.py "question"` | Query across the whole Brain |
| `python3 ~/.claude/scripts/pkb-query.py "question" --save` | Query + save answer to Wiki |
| `python3 ~/.claude/scripts/pkb-query.py --interactive` | Interactive Q&A mode |

### Nightly brain-sync (2 AM cron)
1. Export Apple Notes → `Brain/Apple Notes/`
2. Run git log summaries for active repos → `Brain/Projects/`
3. Run `pkb-process.py` on `Brain/Raw/Inbox/`

---

## Active Projects

| Project | Path | Port | Stack |
|---|---|---|---|
| QoE Platform | `/Users/dm3n/Airbank/Airbank Platform` | 3000 | Next.js 16 + React 19 |
| Airbank Mortgage Platform | `/Users/dm3n/Airbank/Airbank Mortgage Platform` | 3004 | Next.js 16 |
| ROGI | `/Users/dm3n/Projects/rogi` | 3002 | Next.js 16 |

### Folder structure

```
~/
├── Airbank/          # All Airbank repos (QoE Platform, Mortgage Platform, Website, Remotion, etc.)
├── Projects/         # Claude-built side projects (rogi, airbank-lander, VisionClaw, etc.)
├── lab/              # Homelab repos (macintosh, homelab-setup, homelab-work, setup)
└── Archive/          # Old/inactive projects
```

---

## Universal Engineering Rules

Apply in every project, every agent, every session:

- Always use **shadcn/ui** for all UI components
- Do NOT create `middleware.ts` in Next.js 16 — use `proxy.ts`
- Supabase new key format: `sb_publishable_` / `sb_secret_`
- Default Gemini model: `gemini-2.0-flash-001`
- Default Claude model: `claude-sonnet-4-6`
- Supabase project ID: `qlhdslbpgnctshcpiqfv`

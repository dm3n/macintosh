# Knowledge Brain — Obsidian Persistent Context System

> No context is ever lost. Every conversation, session, decision, and project note is captured in a structured, linked knowledge graph — queryable by any AI model at any time.

---

## The Problem It Solves

AI models have no memory between sessions. Every conversation starts blank. Without a persistent context system, you re-explain the same background constantly, lose decisions made in past sessions, and can't build on prior work across tools.

The Brain vault solves this by acting as a permanent second brain that any AI (Claude Code, Claude.ai, future models) reads at the start of every session to instantly understand the full context of who Daniel is, what Airbank is building, and every decision that's been made.

---

## Two Vaults

### 1. Brain Vault — Personal Knowledge Base

**Location:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/`
**Synced via:** iCloud (available on all devices)

```
Brain/
├── Memory/           # AI agent memory files — loaded at session start
│   ├── MEMORY.md     # Index — always loaded by Claude Code
│   ├── user_*.md     # Who Daniel is, preferences, expertise
│   ├── project_*.md  # Active project context
│   ├── feedback_*.md # Corrections and validated approaches
│   └── reference_*.md# External system pointers (Linear, Supabase, etc.)
│
├── Projects/         # Per-project notes
│   ├── Airbank Platform.md
│   ├── Airbank — Road to $1B.md
│   ├── rogi.md
│   └── Git/          # Auto-generated git summaries per repo
│
├── Claude Sessions/  # Every Claude Code session auto-saved as markdown
├── Claude Web Chats/ # claude.ai conversations auto-exported nightly
├── Apple Notes/      # iPhone/Mac notes exported nightly via script
├── People/           # Contacts — investors, advisors, customers
├── Daily/            # Daily notes (template-based)
├── Airbank/          # Airbank company hub note with dataview queries
├── System/           # Automation scripts, LaunchAgents, SOPs
└── Inbox/            # Quick capture, unsorted
```

**Graph colour groups:**

| Colour | Group |
|--------|-------|
| Cyan | MOC hub notes |
| Green | Memory files |
| Purple | Projects |
| Blue | Claude Sessions + Web Chats |
| Orange | Daily notes + Inbox |
| Pink | Apple Notes |
| Amber | People |
| Red | Airbank |
| Grey | System |

---

### 2. Airbank Code Vault — Live Codebase Graph

**Location:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Airbank/`
**Auto-synced:** Every 10 minutes via LaunchAgent

174 linked notes — one per source file across Airbank Platform and Airbank Website. Import relationships between files become wikilinks, creating a navigable dependency graph.

```
Airbank/
├── Home.md                    # Entry point with last-sync timestamp
├── Airbank Platform/
│   ├── Overview.md            # Project hub
│   ├── app/
│   │   ├── api/_index.md      # All API routes (red nodes)
│   │   ├── (auth)/_index.md   # Auth pages (purple nodes)
│   │   └── [route]/page.md    # Per-page notes
│   ├── components/
│   │   ├── _index.md          # Component hub (blue nodes)
│   │   └── [component].md     # Per-component: exports, imports, description
│   └── lib/
│       ├── _index.md          # Library hub (green nodes)
│       └── [module].md        # Per-module: exports, imports
└── Airbank Website/
    └── ...
```

**Graph colour groups:**

| Colour | Group |
|--------|-------|
| Purple | Pages |
| Blue | Components |
| Red | API routes |
| Green | Library |
| Amber | Hooks |
| Cyan | Index/hub nodes |

---

## Automation Stack

### Nightly Brain Export

**Script:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/System/export-brain.sh`
**Schedule:** Every night via LaunchAgent `ca.nodebase.brain-export`

What it does:
1. Exports Apple Notes from iCloud to `Brain/Apple Notes/`
2. Runs `git log` summaries for all repos → `Brain/Projects/Git/`
3. Saves Claude session summaries to `Brain/Claude Sessions/`

### Airbank Vault Sync

**Script:** `~/Airbank/scripts/sync-vault.py`
**Schedule:** Every 10 minutes via LaunchAgent `ca.nodebase.airbank-vault-sync`
**Log:** `~/Airbank/scripts/vault-sync.log`

What it does:
1. `git pull --ff-only` on Airbank Platform + Airbank Website
2. Walks all `.ts`/`.tsx` files in `app/`, `components/`, `lib/`, `hooks/`
3. Parses each file: imports, exports, component names, HTTP methods, description
4. Generates a linked markdown note per file
5. Creates directory index notes
6. Updates `Home.md` with sync timestamp and git status

### Claude Code Memory System

Claude Code reads `Brain/Memory/MEMORY.md` at the start of every session. Memory is written back after each session with new context. Four memory types:

| Type | What it stores |
|------|---------------|
| `user` | Daniel's preferences, expertise, working style |
| `feedback` | Corrections and validated approaches — what to repeat or avoid |
| `project` | Active project state, decisions, constraints |
| `reference` | Where to find things (Linear team IDs, Supabase project IDs, etc.) |

---

## How to Use the Brain

**At session start (automatic):**
Claude Code reads `MEMORY.md` and relevant project notes before doing any work.

**During a session:**
As new decisions are made or context changes, Claude Code writes new memory files immediately.

**Searching the Brain:**
- Obsidian quick switcher (`Cmd+O`) — find any note instantly
- Graph view (`Cmd+G`) — visualise connections between knowledge
- Dataview plugin — query notes like a database (used in the Airbank hub note)
- Full-text search (`Cmd+Shift+F`) — search across all 1,000+ notes

**Adding to the Brain manually:**
Drop notes in `Brain/Inbox/` — they'll be linked from the next session.

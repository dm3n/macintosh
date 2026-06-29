# Knowledge Brain: Self-Maintaining PKB (LLM-WIKI Architecture)

> No context is ever lost. Every conversation, source, decision, and project note is compiled into a structured, interlinked wiki, queryable by any AI model at any time. Knowledge is compiled once at ingest, not re-derived on every query.

The Brain is a personal implementation of Karpathy's **LLM-WIKI.md** pattern: a self-maintaining knowledge base in which the model does the bookkeeping that humans never sustain. The human curates and directs (selects sources, sets direction, oversees synthesis). The model writes, cross-references, and reconciles. That boundary is enforced architecturally, not by discipline.

---

## The Problem It Solves

AI models have no memory between sessions. Every conversation starts blank. Without persistent context you re-explain the same background constantly, lose decisions made in past sessions, and cannot build on prior work across tools.

Classic note systems (Roam, Notion, Obsidian) lower the friction of capture but leave the bookkeeping burden intact. Wikis need editors. Most personal wikis quietly rot. RAG systems avoid the wiki entirely by re-deriving knowledge from raw chunks on every query, so nothing accumulates.

This Brain shifts the maintenance burden to the model. Given a new source, the model reads, summarises, integrates, cross-references, and flags contradictions, producing a persistent compiled artifact rather than an indexed pile of chunks.

---

## Compilation vs Retrieval

| | RAG (retrieve) | This Brain (compile) |
|---|---|---|
| When synthesis happens | Every query | Once, at ingest |
| What accumulates | Nothing | The wiki compounds per source |
| Per-query cost | Re-derive from chunks | Read an already-compiled page |
| Cross-references | Re-discovered each time | Resolved once and stored |
| Contradictions | Invisible | Flagged at ingest and by lint |

Below roughly 100 sources and a few hundred wiki pages, the index file plus the model's context window are sufficient. No embedding or vector infrastructure is required at this scale.

---

## Three Layers

Each layer has a single owner. This is what enforces the human-curates / model-writes separation.

| Layer | Path | Owner | Rule |
|---|---|---|---|
| 1. Raw sources | `Brain/Raw/` | Human | Immutable. Articles, transcripts, notes, papers. Never edited after arrival. Ground truth. |
| 2. Schema | `Brain/System/PKB/schema.md` + `Brain/CLAUDE.md` | Co-authored | Directory structure, page templates, cross-reference conventions, lint criteria. The rules the model is governed by. |
| 3. Wiki | `Brain/Wiki/` | Model | Entirely model-generated. Entity pages, concept pages, SOPs, summaries, an index, a log. The human reads it, the model writes it. |

`Raw/` is sorted into drop zones: `News/`, `Blog/`, `Personal/`, `Company/`, `Research/`, `Conversations/`, `Inbox/`. Processed sources move to `Raw/Processed/`.

`Wiki/` is organised into `Entities/People/`, `Entities/Companies/`, `Concepts/`, `Frameworks/`, `SOPs/`, `Summaries/`, and `Compiled/` (saved query answers).

---

## Three Operational Primitives

Three operations cover all routine interaction with the Brain.

| Primitive | Trigger | Scope | Output | Script |
|---|---|---|---|---|
| **Ingest** | New source in `Raw/` | 1 source, N pages | Summary + entity/concept upserts + index rebuild + log entry | `pkb-process.py` |
| **Query** | A question | `index.md`, K pages | Answer with citations, optionally filed as a new `Compiled/` page | `pkb-query.py` |
| **Lint** | Periodic (nightly) | Entire wiki | Health report + log entry | `pkb-lint.py` |

### Ingest

`python3 ~/.claude/scripts/pkb-process.py`

Reads each pending file in `Raw/`, runs it through Claude against the schema, then writes a summary to `Wiki/Summaries/`, upserts People / Companies / Concepts / SOP pages, archives the original to `Raw/Processed/`, rebuilds `Wiki/index.md`, and appends an `ingest` entry to `Wiki/log.md`. A single ingest can touch a dozen wiki pages. Use `--dry-run` to preview, `--file <path>` for one file.

### Query

`python3 ~/.claude/scripts/pkb-query.py "question"`

Reads `Wiki/index.md` first, selects the most relevant pages across the whole vault within a token budget, and synthesises an answer with sources. With `--save`, a substantive answer is filed back into `Wiki/Compiled/` as a new page and logged. `--interactive` opens a REPL.

### Lint

`python3 ~/.claude/scripts/pkb-lint.py`

The periodic health check. It scans for:

- **Orphan pages**: linkable knowledge pages no other note links to.
- **Broken links / missing entries**: `[[targets]]` referenced but lacking their own page (concepts mentioned but never written up).
- **Stale claims**: pages untouched for more than 120 days, or carrying a `[?]` uncertainty marker.
- **Contradictions**: with `--deep`, an LLM pass over page leads surfaces directly conflicting claims.

Lint writes `Wiki/lint-report.md` and appends a `lint` entry to the log. It never edits the wiki; acting on the report is curation, which stays with the human.

---

## Index and Log (Layer 3 navigation, model-owned)

Two special files govern navigation. Both are regenerated/appended by the scripts. Do not hand-edit.

- **`Wiki/index.md`**: an auto-generated catalog of every wiki page with a one-line summary, organised by category. The query primitive reads this first. At moderate scale this removes the need for any search layer.
- **`Wiki/log.md`**: an append-only chronological record. Every ingest, saved query, and lint run appends one entry formatted `## [YYYY-MM-DD] op | title`, so the log is parseable with standard unix tools (for example `grep '] ingest |' log.md`).

---

## Engine Source

The four scripts that implement the primitives are vendored in this repo at [`scripts/pkb/`](../scripts/pkb/) and installed to `~/.claude/scripts/` by `scripts/install-pkb.sh` (run automatically by `bootstrap.sh`).

| File | Role |
|---|---|
| `pkb_common.py` | Shared helpers: `rebuild_index()` and `append_log()` (the two navigation files). |
| `pkb-process.py` | Ingest primitive. |
| `pkb-query.py` | Query primitive. |
| `pkb-lint.py` | Lint primitive. |

---

## Vault Layout

**Location:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain/`
**Synced via:** iCloud (available on all devices)

```
Brain/
├── CLAUDE.md          # Layer 2: vault-scoped agent context + rules
├── Raw/               # Layer 1: immutable sources (News, Blog, Personal,
│                      #          Company, Research, Conversations, Inbox, Processed)
├── Wiki/              # Layer 3: model-generated knowledge
│   ├── index.md       #   catalog of every page (read first on query)
│   ├── log.md         #   append-only operations log
│   ├── lint-report.md #   latest health check
│   ├── Entities/      #   People/ + Companies/
│   ├── Concepts/      #   frameworks, mental models
│   ├── Frameworks/
│   ├── SOPs/          #   repeatable processes
│   ├── Summaries/     #   one summary per ingested source
│   └── Compiled/      #   saved query answers
├── System/PKB/        # schema.md (Layer 2 rules) + automation
├── Memory/            # Claude Code session memory (MEMORY.md index + topic files)
├── Projects/          # per-project notes + git summaries
├── People/            # contacts: investors, advisors, customers
├── Claude Sessions/   # every Claude Code session auto-summarised
├── Claude Web Chats/  # claude.ai conversations exported nightly
├── Apple Notes/       # iPhone/Mac notes exported nightly
├── Daily/ Standups/   # daily + team notes
└── Inbox/             # quick capture
```

### Memory vs Wiki

These are distinct and complementary. `Memory/MEMORY.md` is the **agent memory index**, loaded at the start of every Claude Code session (who Daniel is, active projects, standing rules, status pointers). `Wiki/index.md` is the **wiki catalog**, read by the query primitive when answering questions against compiled knowledge. Memory is the session bootstrap; the wiki is the compiled corpus.

Four memory types: `user` (preferences, expertise), `feedback` (corrections and validated approaches), `project` (active state, decisions), `reference` (where to find things: Linear team IDs, Supabase project IDs, and so on).

---

## Second Vault: Code Graph

**Location:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Airbank/`
**Auto-synced:** every 10 minutes via LaunchAgent `ca.nodebase.airbank-vault-sync`

One linked note per source file across the mirrored repos. Import relationships become wikilinks, producing a navigable dependency graph. The sync script (`~/Airbank/scripts/sync-vault.py`) pulls each repo, walks `app/`, `components/`, `lib/`, `hooks/`, parses imports / exports / component names / HTTP methods, and writes a markdown note per file plus directory index notes.

---

## Automation Stack

| Job | Schedule | What it does |
|---|---|---|
| Nightly brain-sync | 02:00 daily | Apple Notes export, git history snapshots, **PKB ingest**, **PKB lint**, session summaries |
| Code vault sync | every 10 min | Pull repos, regenerate the code graph, update `Home.md` timestamp |
| Claude Code memory | per session | Read `MEMORY.md` at start, write new memory files during the session |

The nightly brain-sync is where ingest and lint run unattended: new `Raw/` drops get compiled into the wiki, then lint reports on the wiki's health.

---

## How to Use the Brain

**At session start (automatic):** Claude Code reads `MEMORY.md` and relevant project notes before doing any work.

**Add a source:** drop a file into the right `Raw/` subfolder. The nightly ingest compiles it, or run `pkb-process.py --file <path>` now.

**Ask a question across everything:** `pkb-query.py "question"` (add `--save` to file the answer).

**Check wiki health:** `pkb-lint.py` (add `--deep` for a contradiction scan). Read `Wiki/lint-report.md`.

**Browse:** Obsidian quick switcher (`Cmd+O`), graph view (`Cmd+G`), Dataview queries, full-text search (`Cmd+Shift+F`).

---

## Reference

Karpathy, A. *LLM-WIKI.md: A Self-Maintaining Personal Knowledge Base Architecture Using Large Language Models. Field Notes on Compilation-Based Knowledge Accumulation.*

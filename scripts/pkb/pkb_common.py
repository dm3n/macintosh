#!/usr/bin/env python3
"""
PKB Common — shared helpers for the LLM-WIKI knowledge architecture
===================================================================
Implements the two Layer-3 navigation files described in Karpathy's
"LLM-WIKI.md: A Self-Maintaining Personal Knowledge Base Architecture":

  - index.md  → a catalog of every wiki page with a one-line summary,
                organised by category. The query primitive reads this FIRST.
  - log.md    → an append-only chronological record of every operation.
                Entries are formatted '## [YYYY-MM-DD] op | title' so they
                are parseable with standard unix tools.

Shared by all three operational primitives:
  - ingest (pkb-process.py)
  - query  (pkb-query.py)
  - lint   (pkb-lint.py)
"""

import re
from pathlib import Path
from datetime import datetime

BRAIN = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain"
WIKI_PATH = BRAIN / "Wiki"
INDEX_PATH = WIKI_PATH / "index.md"
LOG_PATH = WIKI_PATH / "log.md"

# Categories that make up the wiki catalog, in display order.
INDEX_CATEGORIES = [
    ("People",     WIKI_PATH / "Entities/People"),
    ("Companies",  WIKI_PATH / "Entities/Companies"),
    ("Concepts",   WIKI_PATH / "Concepts"),
    ("Frameworks", WIKI_PATH / "Frameworks"),
    ("SOPs",       WIKI_PATH / "SOPs"),
    ("Summaries",  WIKI_PATH / "Summaries"),
    ("Compiled",   WIKI_PATH / "Compiled"),
]

# Files that are navigation artifacts, not knowledge pages — never cataloged.
RESERVED = {"index.md", "log.md", "lint-report.md"}


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def append_log(op: str, title: str, detail: str = "") -> None:
    """Append an entry to the wiki's append-only operations log.

    Format follows LLM-WIKI: '## [YYYY-MM-DD] op | title' so entries are
    greppable with standard unix tools (e.g. `grep '] ingest |' log.md`).
    `op` is one of: ingest, query, lint.
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text(
            "# Wiki Operations Log\n"
            "*Append-only chronological record. One entry per operation.*\n"
            "*Format: `## [YYYY-MM-DD] op | title` — parseable with standard unix tools.*\n\n"
        )
    title = title.replace("\n", " ").strip()
    entry = f"## [{_today()}] {op} | {title}\n"
    if detail:
        entry += f"{detail.strip()}\n"
    entry += "\n"
    with LOG_PATH.open("a") as fh:
        fh.write(entry)


def _one_line_summary(path: Path) -> str:
    """Extract a one-line summary for a page: the first prose line, skipping
    headings, frontmatter, and the boilerplate metadata lines the ingest
    primitive writes (**Source:**, **Type:**, etc.)."""
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return ""
    skip_prefixes = ("**source", "**type", "**processed", "**asked",
                     "**compiled", "**role", "**relationship", "**sector",
                     "**relevance", "**stage", "**trigger", "**owner",
                     "**last updated", "**contact")
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("---"):
            continue
        if s.lower().startswith(skip_prefixes):
            continue
        s = re.sub(r"[`*_>]", "", s).strip()
        s = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", s)  # flatten wikilinks
        if s:
            return s[:140]
    return ""


def rebuild_index() -> int:
    """Regenerate Wiki/index.md — a catalog of every wiki page with a one-line
    summary, organised by category. The query primitive reads this first; at
    moderate scale this removes the need for any embedding/search infrastructure.
    Returns the number of pages cataloged."""
    WIKI_PATH.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Wiki Index",
        "*Auto-generated catalog of every wiki page. The query primitive reads this first.*",
        f"*Last rebuilt: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
    ]
    total = 0
    active_categories = 0
    for label, folder in INDEX_CATEGORIES:
        if not folder.exists():
            continue
        pages = sorted(p for p in folder.glob("*.md") if p.name not in RESERVED)
        if not pages:
            continue
        active_categories += 1
        lines.append(f"## {label} ({len(pages)})")
        for p in pages:
            summary = _one_line_summary(p)
            entry = f"- [[{p.stem}]]"
            if summary:
                entry += f" — {summary}"
            lines.append(entry)
            total += 1
        lines.append("")
    lines.append("---")
    lines.append(f"*{total} pages cataloged across {active_categories} categories.*")
    INDEX_PATH.write_text("\n".join(lines) + "\n")
    return total


if __name__ == "__main__":
    n = rebuild_index()
    print(f"[pkb] index.md rebuilt — {n} pages cataloged → {INDEX_PATH}")

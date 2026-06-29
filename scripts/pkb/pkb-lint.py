#!/usr/bin/env python3
"""
PKB Lint — the third LLM-WIKI operational primitive (ingest / query / lint)
===========================================================================
Periodic health check over Brain/Wiki/. Per Karpathy's LLM-WIKI architecture,
lint "scans for contradictions, stale claims, orphan pages, and concepts
lacking their own entry. Lint output is itself a log entry."

Deterministic checks (fast, no model call):
  - orphan pages    — knowledge pages no other note links to
  - broken links    — [[targets]] referenced but lacking their own page
                      (i.e. concepts mentioned but never written up)
  - stale pages     — not touched in > STALE_DAYS days, or carrying a [?] marker

Optional model pass (--deep):
  - contradictions  — LLM scan across page leads for conflicting claims

Writes a health report to Brain/Wiki/lint-report.md and appends a one-line
entry to Brain/Wiki/log.md.

Usage:
  python3 pkb-lint.py            # deterministic health check
  python3 pkb-lint.py --deep     # + LLM contradiction scan
  python3 pkb-lint.py --quiet    # write report + log, minimal stdout
"""

import re
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

from pkb_common import BRAIN, WIKI_PATH, append_log

STALE_DAYS = 120
REPORT_PATH = WIKI_PATH / "lint-report.md"

# Knowledge pages that *should* be linked from elsewhere. Summaries and Compiled
# answers are leaf nodes by nature, so they are excluded from the orphan check.
LINKABLE_DIRS = ["Entities/People", "Entities/Companies", "Concepts", "Frameworks", "SOPs"]
ALL_WIKI_DIRS = LINKABLE_DIRS + ["Summaries", "Compiled"]

# Corpus searched for inbound links and outbound references.
CORPUS_DIRS = ["Wiki", "Memory", "Projects", "People", "Daily", "Standups", "Inbox"]

RESERVED = {"index.md", "log.md", "lint-report.md"}


def _norm(s: str) -> str:
    """Normalise a page name / link target so 'Concept Name' and
    'Concept-Name' compare equal."""
    return re.sub(r"[-\s]+", "-", s.strip().lower())


def wiki_pages(dirs):
    pages = []
    for d in dirs:
        folder = WIKI_PATH / d
        if folder.exists():
            pages.extend(p for p in folder.glob("*.md") if p.name not in RESERVED)
    return pages


def corpus_files():
    files = []
    for d in CORPUS_DIRS:
        p = BRAIN / d
        if p.exists():
            files.extend(f for f in p.rglob("*.md") if f.name not in RESERVED)
    return files


def extract_links(text: str):
    # [[Target]] or [[Target|alias]] or [[Target#heading]]
    return set(re.findall(r"\[\[([^\]|#]+)", text))


def days_since(path: Path) -> int:
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - mtime).days


def call_claude(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["claude", "--print", "--output-format", "text", prompt],
            capture_output=True, text=True, timeout=180,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception as e:
        print(f"[pkb-lint] model call failed: {e}", file=sys.stderr)
        return ""


def deep_contradiction_scan(pages) -> str:
    """Feed page leads to Claude to surface contradictions."""
    leads = []
    for p in pages:
        try:
            head = p.read_text(errors="replace")[:600]
        except Exception:
            continue
        leads.append(f"### {p.stem}\n{head}")
    blob = "\n\n".join(leads)[:120_000]
    prompt = (
        "You are linting Daniel's personal knowledge wiki for CONTRADICTIONS only.\n"
        "Below are leads from wiki pages. List any pairs of pages that make "
        "directly conflicting factual claims (dates, roles, numbers, status). "
        "For each, name both pages and the conflict in one line. If none, reply "
        "'No contradictions found.'\n\n" + blob
    )
    return call_claude(prompt) or "Model scan returned no output."


def main():
    ap = argparse.ArgumentParser(description="PKB Lint — wiki health check")
    ap.add_argument("--deep", action="store_true", help="add LLM contradiction scan")
    ap.add_argument("--quiet", action="store_true", help="minimal stdout")
    args = ap.parse_args()

    def say(*a):
        if not args.quiet:
            print(*a)

    linkable = wiki_pages(LINKABLE_DIRS)
    all_pages = wiki_pages(ALL_WIKI_DIRS)
    corpus = corpus_files()

    # Map of every normalised page name that exists.
    existing = {_norm(p.stem) for p in all_pages}

    # All inbound links used anywhere in the corpus.
    used_links = set()
    for f in corpus:
        try:
            used_links |= {_norm(t) for t in extract_links(f.read_text(errors="replace"))}
        except Exception:
            continue

    # 1) Orphans — linkable pages nothing points to.
    orphans = [p for p in linkable if _norm(p.stem) not in used_links]

    # 2) Broken links — referenced targets that have no page of their own.
    broken = sorted(used_links - existing)

    # 3) Stale — old mtime or [?] uncertainty marker.
    stale = []
    for p in all_pages:
        try:
            uncertain = "[?]" in p.read_text(errors="replace")
        except Exception:
            uncertain = False
        age = days_since(p)
        if age > STALE_DAYS or uncertain:
            reason = []
            if age > STALE_DAYS:
                reason.append(f"{age}d untouched")
            if uncertain:
                reason.append("[?] marker")
            stale.append((p, ", ".join(reason)))

    now = datetime.now()
    report = [
        "# Wiki Lint Report",
        f"*Generated: {now.strftime('%Y-%m-%d %H:%M')}*",
        f"*Scope: {len(all_pages)} wiki pages, {len(corpus)} corpus files.*",
        "",
        "## Summary",
        f"- Orphan pages (linkable, unlinked): **{len(orphans)}**",
        f"- Broken links (concepts lacking an entry): **{len(broken)}**",
        f"- Stale pages (>{STALE_DAYS}d or `[?]`): **{len(stale)}**",
        "",
    ]

    report.append("## Orphan Pages")
    report.append("*Knowledge pages no other note links to — wire them in or retire them.*")
    report += ([f"- [[{p.stem}]] ({p.parent.name})" for p in orphans] or ["- None ✓"])
    report.append("")

    report.append("## Broken Links / Missing Entries")
    report.append("*Referenced via `[[...]]` but no page exists — candidates to write up.*")
    report += ([f"- `[[{t}]]`" for t in broken[:60]] or ["- None ✓"])
    if len(broken) > 60:
        report.append(f"- … and {len(broken) - 60} more")
    report.append("")

    report.append("## Stale Pages")
    report.append(f"*Not touched in >{STALE_DAYS} days, or carrying a `[?]` uncertainty marker.*")
    report += ([f"- [[{p.stem}]] — {why}" for p, why in stale] or ["- None ✓"])
    report.append("")

    if args.deep:
        say("[pkb-lint] running LLM contradiction scan…")
        report.append("## Contradiction Scan (LLM)")
        report.append(deep_contradiction_scan(all_pages))
        report.append("")

    report.append("---")
    report.append("*Generated by `pkb-lint.py` — the LLM-WIKI lint primitive.*")

    REPORT_PATH.write_text("\n".join(report) + "\n")

    detail = (f"{len(orphans)} orphans, {len(broken)} broken links, "
              f"{len(stale)} stale" + (", +LLM contradiction scan" if args.deep else ""))
    append_log("lint", "health check", detail)

    say(f"[pkb-lint] {detail}")
    say(f"[pkb-lint] report → {REPORT_PATH}")


if __name__ == "__main__":
    main()

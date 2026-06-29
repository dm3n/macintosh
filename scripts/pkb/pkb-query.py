#!/usr/bin/env python3
"""
PKB Query — Ask complex questions across the entire Knowledge Brain
====================================================================
Searches Brain/Wiki/, Brain/Memory/, Brain/Projects/, Brain/Claude Sessions/,
and Brain/People/ to answer questions with full context.

Good answers are optionally saved back to Brain/Wiki/Compiled/

Usage:
  python3 pkb-query.py "what do we know about private credit markets?"
  python3 pkb-query.py "what has Andrew Auslander said about Airbank?" --save
  python3 pkb-query.py --interactive         # REPL mode
"""

import os
import sys
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Shared LLM-WIKI navigation helpers (index.md catalog + log.md op log).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkb_common import append_log, INDEX_PATH

BRAIN = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain"

# Search corpus — ordered by priority
SEARCH_DIRS = [
    BRAIN / "Wiki",
    BRAIN / "Memory",
    BRAIN / "People",
    BRAIN / "Projects",
    BRAIN / "Airbank",
    BRAIN / "Apple Notes",
    BRAIN / "Claude Sessions",
    BRAIN / "Claude Web Chats",
]

COMPILED_PATH = BRAIN / "Wiki/Compiled"
MAX_CONTEXT_CHARS = 80_000  # ~20k tokens
MAX_FILE_CHARS = 3_000      # cap per file to spread context


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:60]


def collect_brain_files() -> list[Path]:
    """Collect all markdown files from search corpus."""
    files = []
    for search_dir in SEARCH_DIRS:
        if search_dir.exists():
            files.extend(search_dir.rglob("*.md"))
    return files


def keyword_score(content: str, query: str) -> int:
    """Simple keyword relevance score."""
    query_words = set(re.findall(r"\w+", query.lower()))
    content_lower = content.lower()
    return sum(content_lower.count(word) for word in query_words if len(word) > 3)


def select_relevant_files(files: list[Path], query: str, max_chars: int) -> list[tuple[Path, str]]:
    """Score and select the most relevant files within token budget."""
    scored = []
    for f in files:
        try:
            content = f.read_text(errors="replace")
            score = keyword_score(content, query)
            if score > 0:
                scored.append((score, f, content))
        except Exception:
            continue

    # Sort by relevance descending
    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    total_chars = 0
    for score, path, content in scored:
        truncated = content[:MAX_FILE_CHARS]
        if total_chars + len(truncated) > max_chars:
            break
        selected.append((path, truncated))
        total_chars += len(truncated)

    return selected


def build_query_prompt(question: str, context_files: list[tuple[Path, str]]) -> str:
    context_blocks = ""
    for path, content in context_files:
        # Show relative path from BRAIN for readability
        try:
            rel = path.relative_to(BRAIN)
        except ValueError:
            rel = path
        context_blocks += f"\n\n---\n**File:** `{rel}`\n\n{content}"

    return f"""You are answering a question for Daniel Edgar (founder of Airbank) using his Personal Knowledge Brain.

## Question
{question}

## Brain Context ({len(context_files)} relevant files)
{context_blocks}

---

Answer the question thoroughly using only information from the Brain context above.
- Be specific — quote or reference specific files/people/dates where relevant
- If the answer spans multiple files, synthesise them
- If information is incomplete or contradictory, say so explicitly
- Format your answer in clear markdown
- End with a "Sources" section listing the files that informed your answer

If the context doesn't contain enough information to answer well, say so directly.
"""


def call_claude(prompt: str) -> str:
    """Call claude CLI."""
    try:
        result = subprocess.run(
            ["claude", "--print", "--output-format", "text", prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"[pkb-query] Claude error: {result.stderr}", file=sys.stderr)
            return ""
    except FileNotFoundError:
        return call_anthropic_sdk(prompt)
    except Exception as e:
        print(f"[pkb-query] Error: {e}", file=sys.stderr)
        return ""


def call_anthropic_sdk(prompt: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except ImportError:
        print("[pkb-query] Neither claude CLI nor anthropic SDK available.", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"[pkb-query] Anthropic SDK error: {e}", file=sys.stderr)
        return ""


def save_answer(question: str, answer: str) -> Path:
    """Save a high-quality answer to Wiki/Compiled/."""
    COMPILED_PATH.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    slug = slugify(question)
    filename = f"{date_str}-{slug}.md"
    out_path = COMPILED_PATH / filename

    content = f"""# Q: {question}
**Asked:** {date_str}
**Compiled by:** PKB Query

---

{answer}

---
*Auto-saved to Brain/Wiki/Compiled/ — {now.strftime('%Y-%m-%d %H:%M')}*
"""
    out_path.write_text(content)
    return out_path


def query(question: str, save: bool = False) -> str:
    """Run a query against the Brain and return the answer."""
    print(f"[pkb-query] Searching Brain for: {question[:80]}...", file=sys.stderr)

    all_files = collect_brain_files()
    print(f"[pkb-query] Corpus: {len(all_files)} files", file=sys.stderr)

    relevant = select_relevant_files(all_files, question, MAX_CONTEXT_CHARS)
    print(f"[pkb-query] Selected {len(relevant)} relevant files", file=sys.stderr)

    if not relevant:
        return "No relevant files found in the Brain for this question."

    # LLM-WIKI: read the wiki index first so the model navigates the catalog
    # before diving into individual pages.
    if INDEX_PATH.exists():
        try:
            index_text = INDEX_PATH.read_text(errors="replace")[:6000]
            relevant.insert(0, (INDEX_PATH, index_text))
        except Exception:
            pass

    prompt = build_query_prompt(question, relevant)
    answer = call_claude(prompt)

    if not answer:
        return "Failed to get a response."

    if save:
        saved_path = save_answer(question, answer)
        print(f"[pkb-query] Saved to: {saved_path}", file=sys.stderr)
        # A substantive, filed answer is a new wiki page → log it.
        append_log("query", question[:80], f"compiled → {saved_path.name}")

    return answer


def interactive_mode():
    """REPL interface for Brain queries."""
    print("PKB Query — Interactive Mode")
    print("Commands: :save (save last answer), :quit (exit)")
    print("=" * 50)

    last_question = ""
    last_answer = ""

    while True:
        try:
            question = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[pkb-query] Exiting.")
            break

        if not question:
            continue

        if question == ":quit":
            break

        if question == ":save":
            if last_answer and last_question:
                saved = save_answer(last_question, last_answer)
                print(f"Saved → {saved}")
            else:
                print("Nothing to save yet.")
            continue

        last_question = question
        last_answer = query(question, save=False)
        print("\n" + last_answer)


def main():
    parser = argparse.ArgumentParser(description="PKB Query — Ask your Personal Knowledge Brain")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--save", action="store_true", help="Save answer to Wiki/Compiled/")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive REPL mode")
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
        return

    if not args.question:
        parser.print_help()
        sys.exit(1)

    answer = query(args.question, save=args.save)
    print(answer)


if __name__ == "__main__":
    main()

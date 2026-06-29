#!/usr/bin/env python3
"""
PKB Processor — Personal Knowledge Brain
=========================================
Reads Brain/Raw/, processes each file through Claude,
writes summaries, entities, and wiki pages back to Brain/Wiki/.

Usage:
  python3 pkb-process.py              # process all pending Raw/ files
  python3 pkb-process.py --dry-run    # show what would be processed
  python3 pkb-process.py --file path  # process a single specific file
"""

import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Shared LLM-WIKI navigation helpers (index.md catalog + log.md op log).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pkb_common import append_log, rebuild_index

BRAIN = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain"
RAW_PATH = BRAIN / "Raw"
WIKI_PATH = BRAIN / "Wiki"
SCHEMA_PATH = BRAIN / "System/PKB/schema.md"
PROCESSED_PATH = RAW_PATH / "Processed"
SUMMARIES_PATH = WIKI_PATH / "Summaries"
ENTITIES_PEOPLE = WIKI_PATH / "Entities/People"
ENTITIES_COMPANIES = WIKI_PATH / "Entities/Companies"
CONCEPTS_PATH = WIKI_PATH / "Concepts"
SOPS_PATH = WIKI_PATH / "SOPs"
COMPILED_PATH = WIKI_PATH / "Compiled"

SOURCE_FOLDERS = {
    "News": "news",
    "Blog": "blog",
    "Personal": "personal",
    "Company": "company",
    "Research": "research",
    "Conversations": "conversation",
    "Inbox": "unknown",
}

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:60]

def read_schema() -> str:
    if SCHEMA_PATH.exists():
        return SCHEMA_PATH.read_text()
    return ""

def get_pending_files() -> list[tuple[Path, str]]:
    """Return list of (file_path, source_type) for unprocessed raw files."""
    pending = []
    for folder_name, source_type in SOURCE_FOLDERS.items():
        folder = RAW_PATH / folder_name
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            if f.parent.name != "Processed":
                pending.append((f, source_type))
    return pending

def call_claude(prompt: str) -> str:
    """Call claude CLI to process content. Returns the response text."""
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
            print(f"[pkb] Claude error: {result.stderr}", file=sys.stderr)
            return ""
    except FileNotFoundError:
        # Fallback: try anthropic SDK
        return call_anthropic_sdk(prompt)
    except Exception as e:
        print(f"[pkb] Error calling claude: {e}", file=sys.stderr)
        return ""

def call_anthropic_sdk(prompt: str) -> str:
    """Fallback: use anthropic SDK directly if claude CLI unavailable."""
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
        print("[pkb] Neither claude CLI nor anthropic SDK available.", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"[pkb] Anthropic SDK error: {e}", file=sys.stderr)
        return ""

def build_processing_prompt(content: str, source_type: str, filename: str, schema: str) -> str:
    return f"""You are processing a file for Daniel's Personal Knowledge Brain (PKB).

## PKB Schema (your rules)
{schema}

## Source File
**Filename:** {filename}
**Detected Type:** {source_type}

## Content
{content}

---

Process this source according to the PKB schema. Return a JSON object with this exact structure:

```json
{{
  "source_type": "{source_type}",
  "summary": {{
    "title": "Short descriptive title for this source",
    "bullets": ["key point 1", "key point 2", "key point 3"],
    "paragraph": "1-2 sentence synthesis"
  }},
  "entities": {{
    "people": [
      {{
        "name": "Full Name",
        "role": "Title at Company",
        "company": "Company Name",
        "relationship": "investor|customer|advisor|partner|competitor|reference|unknown",
        "key_insight": "What's notable about them from this source",
        "context": "1-2 sentences about who they are"
      }}
    ],
    "companies": [
      {{
        "name": "Company Name",
        "sector": "sector",
        "relevance": "competitor|customer|partner|investor|reference",
        "description": "what they do in 1 sentence",
        "airbank_relevance": "why this matters to Airbank"
      }}
    ]
  }},
  "concepts": [
    {{
      "name": "Concept Name",
      "type": "framework|mental-model|principle|method",
      "definition": "clear 1-2 sentence definition",
      "application": "how this applies to Daniel or Airbank",
      "is_new": true
    }}
  ],
  "sop_trigger": false,
  "sop_details": null,
  "action_items": ["action 1", "action 2"],
  "tags": ["#tag1", "#tag2"],
  "cross_refs": ["[[Existing Note Name]]", "[[Another Note]]"],
  "key_decisions": []
}}
```

Return ONLY valid JSON. No markdown fences, no explanation, just the JSON object.
"""

def write_summary(source_file: Path, source_type: str, processed: dict) -> Path:
    """Write summary file to Wiki/Summaries/."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    slug = slugify(processed["summary"]["title"])
    filename = f"{date_str}-{slug}.md"
    out_path = SUMMARIES_PATH / filename
    SUMMARIES_PATH.mkdir(parents=True, exist_ok=True)

    tags = " ".join(processed.get("tags", []))
    bullets = "\n".join(f"- {b}" for b in processed["summary"]["bullets"])
    action_items = "\n".join(f"- [ ] {a}" for a in processed.get("action_items", []))
    cross_refs = "\n".join(processed.get("cross_refs", []))

    content = f"""# {processed['summary']['title']}

**Source:** `{source_file.name}`
**Type:** {source_type}
**Processed:** {date_str}
**Tags:** {tags}

## Summary
{processed['summary']['paragraph']}

## Key Points
{bullets}
"""
    if action_items:
        content += f"\n## Action Items\n{action_items}\n"
    if cross_refs:
        content += f"\n## Related\n{cross_refs}\n"

    content += f"\n---\n*Auto-processed by PKB — {now.strftime('%Y-%m-%d %H:%M')}*\n"

    out_path.write_text(content)
    return out_path

def upsert_person_page(person: dict, source_file: Path) -> Path:
    """Create or update a person wiki page."""
    ENTITIES_PEOPLE.mkdir(parents=True, exist_ok=True)
    name = person["name"]
    filename = f"{name.replace(' ', '-')}.md"
    page_path = ENTITIES_PEOPLE / filename
    now = datetime.now().strftime("%Y-%m-%d")

    interaction = f"- {now} — {person.get('key_insight', 'Referenced in source')} · [[{source_file.stem}]]"

    if page_path.exists():
        # Append interaction to existing page
        existing = page_path.read_text()
        if "## Interactions" in existing:
            existing = existing.replace(
                "## Interactions\n",
                f"## Interactions\n{interaction}\n"
            )
        else:
            existing += f"\n## Interactions\n{interaction}\n"
        page_path.write_text(existing)
    else:
        # Create new page
        content = f"""# {name}
**Role:** {person.get('role', 'Unknown')}, {person.get('company', 'Unknown')}
**Relationship:** {person.get('relationship', 'unknown')}

## Context
{person.get('context', '')}

## Interactions
{interaction}

## Key Insights
- {person.get('key_insight', '')}

## Sources
- [[{source_file.stem}]] — {now}
"""
        page_path.write_text(content)

    return page_path

def upsert_company_page(company: dict, source_file: Path) -> Path:
    """Create or update a company wiki page."""
    ENTITIES_COMPANIES.mkdir(parents=True, exist_ok=True)
    name = company["name"]
    filename = f"{name.replace(' ', '-')}.md"
    page_path = ENTITIES_COMPANIES / filename
    now = datetime.now().strftime("%Y-%m-%d")

    if page_path.exists():
        existing = page_path.read_text()
        if "## Sources" in existing:
            existing = existing.replace(
                "## Sources\n",
                f"## Sources\n- [[{source_file.stem}]] — {now}\n"
            )
            page_path.write_text(existing)
    else:
        content = f"""# {name}
**Sector:** {company.get('sector', 'Unknown')}
**Relevance:** {company.get('relevance', 'reference')}

## What They Do
{company.get('description', '')}

## Relevance to Airbank
{company.get('airbank_relevance', '')}

## Key People

## Sources
- [[{source_file.stem}]] — {now}
"""
        page_path.write_text(content)

    return page_path

def upsert_concept_page(concept: dict, source_file: Path) -> Path:
    """Create or update a concept wiki page."""
    CONCEPTS_PATH.mkdir(parents=True, exist_ok=True)
    name = concept["name"]
    filename = f"{name.replace(' ', '-')}.md"
    page_path = CONCEPTS_PATH / filename
    now = datetime.now().strftime("%Y-%m-%d")

    if page_path.exists() and not concept.get("is_new", False):
        return page_path  # Don't overwrite existing concept pages unless flagged

    content = f"""# {name}
**Type:** {concept.get('type', 'concept')}
**Source:** [[{source_file.stem}]]

## Definition
{concept.get('definition', '')}

## Application
{concept.get('application', '')}

## Related

---
*Created by PKB — {now}*
"""
    page_path.write_text(content)
    return page_path

def create_sop(sop_details: dict, source_file: Path) -> Path:
    """Create a new SOP page."""
    SOPS_PATH.mkdir(parents=True, exist_ok=True)
    name = sop_details.get("name", "Unnamed Process")
    filename = f"SOP - {name.replace(' ', '-')}.md"
    page_path = SOPS_PATH / filename
    now = datetime.now().strftime("%Y-%m-%d")

    steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sop_details.get("steps", [])))
    content = f"""# SOP: {name}
**Trigger:** {sop_details.get('trigger', 'When needed')}
**Owner:** Daniel
**Last Updated:** {now}

## Steps
{steps}

## Notes
{sop_details.get('notes', '')}

## Sources
- [[{source_file.stem}]] — {now}
"""
    page_path.write_text(content)
    return page_path

def archive_file(source_file: Path):
    """Move processed file to Raw/Processed/."""
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_PATH / source_file.name
    # Handle name collisions
    if dest.exists():
        stem = source_file.stem
        suffix = source_file.suffix
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = PROCESSED_PATH / f"{stem}-{now}{suffix}"
    source_file.rename(dest)

def process_file(source_file: Path, source_type: str, dry_run: bool = False) -> bool:
    """Process a single raw file through the PKB pipeline."""
    print(f"[pkb] Processing: {source_file.name} ({source_type})")

    content = source_file.read_text()
    if not content.strip():
        print(f"[pkb] Skipping empty file: {source_file.name}")
        return False

    if dry_run:
        print(f"  → Would process {source_file.name} as {source_type}")
        return True

    schema = read_schema()
    prompt = build_processing_prompt(content, source_type, source_file.name, schema)

    raw_response = call_claude(prompt)
    if not raw_response:
        print(f"[pkb] No response for {source_file.name}, skipping.", file=sys.stderr)
        return False

    # Parse JSON response
    try:
        # Strip any accidental markdown fences
        clean = re.sub(r"^```json\n?", "", raw_response.strip())
        clean = re.sub(r"\n?```$", "", clean)
        processed = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"[pkb] JSON parse error for {source_file.name}: {e}", file=sys.stderr)
        print(f"[pkb] Raw response: {raw_response[:500]}", file=sys.stderr)
        return False

    # Write summary
    summary_path = write_summary(source_file, source_type, processed)
    print(f"  → Summary: {summary_path.name}")

    # Upsert entity pages
    for person in processed.get("entities", {}).get("people", []):
        person_path = upsert_person_page(person, source_file)
        print(f"  → Person: {person_path.name}")

    for company in processed.get("entities", {}).get("companies", []):
        company_path = upsert_company_page(company, source_file)
        print(f"  → Company: {company_path.name}")

    # Upsert concept pages
    for concept in processed.get("concepts", []):
        concept_path = upsert_concept_page(concept, source_file)
        print(f"  → Concept: {concept_path.name}")

    # Create SOP if triggered
    if processed.get("sop_trigger") and processed.get("sop_details"):
        sop_path = create_sop(processed["sop_details"], source_file)
        print(f"  → SOP: {sop_path.name}")

    # Archive original
    archive_file(source_file)
    print(f"  → Archived to Raw/Processed/")

    # Append an ingest entry to the wiki operations log (LLM-WIKI primitive).
    people = len(processed.get("entities", {}).get("people", []))
    companies = len(processed.get("entities", {}).get("companies", []))
    concepts = len(processed.get("concepts", []))
    append_log(
        "ingest",
        processed["summary"]["title"],
        f"source: {source_file.name} ({source_type}) · "
        f"{people} people, {companies} companies, {concepts} concepts",
    )

    return True

def main():
    parser = argparse.ArgumentParser(description="PKB Processor — Personal Knowledge Brain")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without doing it")
    parser.add_argument("--file", type=str, help="Process a single specific file")
    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file).expanduser()
        if not file_path.exists():
            print(f"[pkb] File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        # Detect source type from parent folder or default to unknown
        source_type = SOURCE_FOLDERS.get(file_path.parent.name, "unknown")
        process_file(file_path, source_type, dry_run=args.dry_run)
        if not args.dry_run:
            n = rebuild_index()
            print(f"[pkb] index.md rebuilt — {n} pages cataloged.")
        return

    pending = get_pending_files()
    if not pending:
        print("[pkb] No pending files in Raw/ — nothing to process.")
        return

    print(f"[pkb] Found {len(pending)} file(s) to process.")
    processed_count = 0
    for file_path, source_type in pending:
        if process_file(file_path, source_type, dry_run=args.dry_run):
            processed_count += 1

    print(f"[pkb] Done. Processed {processed_count}/{len(pending)} files.")

    # Rebuild the wiki catalog so index.md reflects every new/updated page.
    if processed_count and not args.dry_run:
        n = rebuild_index()
        print(f"[pkb] index.md rebuilt — {n} pages cataloged.")

if __name__ == "__main__":
    main()

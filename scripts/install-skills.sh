#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$ROOT_DIR/skills"
SKILLS_DEST="$HOME/.claude/skills/macintosh"
CLAUDE_MD="$HOME/.claude/CLAUDE.md"

log() {
  printf '[macintosh-skills] %s\n' "$*"
}

# ── Install skill files ───────────────────────────────────────────────────────

mkdir -p "$SKILLS_DEST"

skill_names=()
for skill_file in "$SKILLS_SRC"/*.md; do
  [ -f "$skill_file" ] || continue
  skill_name="$(basename "$skill_file" .md)"
  cp "$skill_file" "$SKILLS_DEST/$skill_name.md"
  skill_names+=("$skill_name")
  log "Installed skill: $skill_name"
done

log "Skills installed to $SKILLS_DEST"

# ── Update ~/.claude/CLAUDE.md ────────────────────────────────────────────────

if [ ! -f "$CLAUDE_MD" ]; then
  log "~/.claude/CLAUDE.md not found — skipping CLAUDE.md update"
  log "Manually add the macintosh skills section if needed"
  exit 0
fi

MARKER_START="<!-- macintosh-skills-start -->"
MARKER_END="<!-- macintosh-skills-end -->"

# Build the skills list
skills_list=""
for name in "${skill_names[@]}"; do
  skills_list="${skills_list}- ${name}: ~/.claude/skills/macintosh/${name}.md"$'\n'
done

NEW_BLOCK="${MARKER_START}
## Macintosh Skills

The following custom skills are available via the Skill tool. Use them alongside superpowers.

${skills_list}
${MARKER_END}"

if grep -q "$MARKER_START" "$CLAUDE_MD" 2>/dev/null; then
  # Replace existing block using awk for portability
  awk -v start="$MARKER_START" -v end="$MARKER_END" -v block="$NEW_BLOCK" '
    $0 == start { skip=1; print block; next }
    skip && $0 == end { skip=0; next }
    !skip { print }
  ' "$CLAUDE_MD" > "$CLAUDE_MD.tmp" && mv "$CLAUDE_MD.tmp" "$CLAUDE_MD"
  log "Updated macintosh skills section in $CLAUDE_MD"
else
  printf '\n%s\n' "$NEW_BLOCK" >> "$CLAUDE_MD"
  log "Appended macintosh skills section to $CLAUDE_MD"
fi

log "Skills setup complete — restart Claude Code to pick up new skills"

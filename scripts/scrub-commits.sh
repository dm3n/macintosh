#!/bin/bash
# Scrub all AI trademark references from commit messages across all repos
# Removes: Claude, Lovable, Co-Authored-By AI lines, Generated-with lines

set -e

GFR="/Users/dm3n/Library/Python/3.9/bin/git-filter-repo"
WORK_DIR="/tmp/scrub-repos"
GITHUB_USER="dm3n"

REPOS=(
  homelab
  airbank
  uncertainty-propagation
  nodebase
  rogi-mortgage-navigator
  prettybgrounding
  nodebase-dev-test
  newmount-saas
  ratestore
  newmount-os-95
  creator-university
  newmount-project-compass
  openCV-HandTracking
  NassauGolf
)

# Python callback to rewrite each commit message
read -r -d '' CALLBACK << 'PYEOF'
import re

def clean(msg):
    lines = msg.decode('utf-8', errors='replace').splitlines()
    out = []
    for line in lines:
        # Drop Co-Authored-By AI lines
        if re.search(r'Co-Authored-By:.*Claude', line, re.IGNORECASE):
            continue
        # Drop "Generated with Claude Code" lines
        if re.search(r'Generated with \[?Claude', line, re.IGNORECASE):
            continue
        # Drop standalone robot emoji + Claude lines
        if re.search(r'🤖.*Claude', line, re.IGNORECASE):
            continue
        # Replace remaining Claude/Lovable occurrences
        line = re.sub(r'\bClaude\s+Code\b', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\bClaude\s+Sonnet[^\s]*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\bClaude\s+Opus[^\s]*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\bClaude\b', '', line, flags=re.IGNORECASE)
        line = re.sub(r'\bLovable\b', '', line, flags=re.IGNORECASE)
        # Clean up leftover double spaces or trailing whitespace
        line = re.sub(r'  +', ' ', line).rstrip()
        out.append(line)
    # Strip trailing blank lines
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out).encode('utf-8')

message = clean(message)
PYEOF

mkdir -p "$WORK_DIR"

for REPO in "${REPOS[@]}"; do
  echo ""
  echo "══════════════════════════════════════"
  echo "  $REPO"
  echo "══════════════════════════════════════"

  CLONE_DIR="$WORK_DIR/$REPO"
  rm -rf "$CLONE_DIR"

  echo "  Cloning..."
  if ! gh repo clone "$GITHUB_USER/$REPO" "$CLONE_DIR" -- --quiet 2>/dev/null; then
    echo "  SKIP — repo not found or no access"
    continue
  fi

  cd "$CLONE_DIR"

  # Check if any commits contain the trademarks
  COUNT=$(git log --all --format="%B" | grep -ciE 'claude|lovable' || true)
  if [ "$COUNT" -eq 0 ]; then
    echo "  CLEAN — no matches found, skipping"
    cd /
    continue
  fi

  echo "  Found $COUNT line(s) to scrub — rewriting history..."
  $GFR --message-callback "$CALLBACK" --force --quiet

  echo "  Force pushing..."
  git push --force --all --quiet
  git push --force --tags --quiet 2>/dev/null || true

  echo "  Done."
  cd /
done

echo ""
echo "══════════════════════════════════════"
echo "  All repos processed."
echo "══════════════════════════════════════"
rm -rf "$WORK_DIR"

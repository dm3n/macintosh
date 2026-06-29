#!/usr/bin/env bash
set -euo pipefail

# Installs the Personal Knowledge Brain (LLM-WIKI) engine scripts into the
# Claude Code scripts directory, where the nightly brain-sync invokes them.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${PKB_SCRIPTS_DIR:-$HOME/.claude/scripts}"

log() { printf '[macintosh-pkb] %s\n' "$*"; }

mkdir -p "$DEST"

for f in pkb_common.py pkb-process.py pkb-query.py pkb-lint.py; do
  cp "$ROOT_DIR/scripts/pkb/$f" "$DEST/$f"
  log "Installed $f"
done

chmod +x "$DEST/pkb-process.py" "$DEST/pkb-query.py" "$DEST/pkb-lint.py" 2>/dev/null || true

log "PKB engine installed to $DEST"
log "  ingest: python3 $DEST/pkb-process.py"
log "  query:  python3 $DEST/pkb-query.py \"question\""
log "  lint:   python3 $DEST/pkb-lint.py"

#!/usr/bin/env bash
set -euo pipefail

MACINTOSH_REPO="${MACINTOSH_REPO:-https://github.com/dm3n/macintosh.git}"
MACINTOSH_DIR="${MACINTOSH_DIR:-$HOME/lab/homelab-macintosh}"

log() {
  printf '[macintosh-install] %s\n' "$*"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "Missing required command: $cmd"
    exit 1
  fi
}

require_cmd git
require_cmd bash

mkdir -p "$(dirname "$MACINTOSH_DIR")"

if [ -d "$MACINTOSH_DIR/.git" ]; then
  log "Existing install detected at $MACINTOSH_DIR"
  git -C "$MACINTOSH_DIR" remote get-url origin >/dev/null 2>&1 || true
  log "Updating repository (fast-forward only)"
  git -C "$MACINTOSH_DIR" pull --ff-only
else
  log "Cloning $MACINTOSH_REPO -> $MACINTOSH_DIR"
  git clone "$MACINTOSH_REPO" "$MACINTOSH_DIR"
fi

log "Running bootstrap"
bash "$MACINTOSH_DIR/scripts/bootstrap.sh"

log "Install complete"
log "Next: cd $MACINTOSH_DIR && make validate"

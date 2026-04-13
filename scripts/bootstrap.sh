#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  printf '[macintosh-bootstrap] %s\n' "$*"
}

warn() {
  printf '[macintosh-bootstrap] WARNING: %s\n' "$*"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "Missing required command: $cmd"
    exit 1
  fi
}

require_cmd bash
require_cmd git

if ! command -v docker >/dev/null 2>&1; then
  warn "docker not found; homelab stack cannot run yet"
fi

if [ ! -f "$ROOT_DIR/homelab/.env" ]; then
  cp "$ROOT_DIR/homelab/.env.example" "$ROOT_DIR/homelab/.env"
  log "Created homelab/.env from .env.example"
else
  log "homelab/.env already exists"
fi

chmod +x "$ROOT_DIR/scripts"/*.sh "$ROOT_DIR/homelab/scripts"/*.sh

log "Running repository validation"
"$ROOT_DIR/scripts/validate-repo.sh"

log "Bootstrap complete"

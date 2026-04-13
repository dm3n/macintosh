#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass() {
  printf '[PASS] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  exit 1
}

warn() {
  printf '[WARN] %s\n' "$1"
}

required_files=(
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/CONTRIBUTING.md"
  "$ROOT_DIR/LICENSE"
  "$ROOT_DIR/homelab/docker-compose.yml"
  "$ROOT_DIR/homelab/.env.example"
  "$ROOT_DIR/homelab/database/schema.sql"
  "$ROOT_DIR/scripts/install.sh"
  "$ROOT_DIR/scripts/bootstrap.sh"
  "$ROOT_DIR/services/package.json"
  "$ROOT_DIR/services/package-lock.json"
  "$ROOT_DIR/services/Dockerfile"
)

for f in "${required_files[@]}"; do
  [ -f "$f" ] || fail "Missing required file: ${f#$ROOT_DIR/}"
done
pass "Required files exist"

if rg -n "gemini-2\\.0|Gemini 2\\.0|gemini-2-0|Warp \\+ Zsh|Terminal: \\*\\*Warp\\*\\*|replaced Warp" \
  "$ROOT_DIR/README.md" "$ROOT_DIR/docs" >/dev/null; then
  fail "Found stale platform/model references (Gemini 2.0 or Warp)."
fi
pass "No stale model/terminal references"

if ! rg -n "Gemini 3|gemini-3" "$ROOT_DIR/README.md" "$ROOT_DIR/docs" >/dev/null; then
  fail "Gemini 3 reference missing from docs"
fi
pass "Gemini 3 is documented"

if rg -n "telegram|Telegram|TELEGRAM" "$ROOT_DIR/README.md" "$ROOT_DIR/docs" "$ROOT_DIR/homelab" "$ROOT_DIR/services" >/dev/null; then
  fail "Found stale Telegram references; approval flow must be Linear-based."
fi
pass "No stale Telegram references"

service_dirs=(
  "$ROOT_DIR/services/orchestrator"
  "$ROOT_DIR/services/mcp-gateway"
  "$ROOT_DIR/services/approval-gateway"
  "$ROOT_DIR/services/executor"
  "$ROOT_DIR/services/agents/code"
  "$ROOT_DIR/services/agents/email"
  "$ROOT_DIR/services/agents/calendar"
  "$ROOT_DIR/services/agents/todo"
  "$ROOT_DIR/services/agents/linear"
  "$ROOT_DIR/services/agents/slack"
)

for d in "${service_dirs[@]}"; do
  [ -d "$d" ] || fail "Missing service directory: ${d#$ROOT_DIR/}"
  [ -f "$d/README.md" ] || warn "Missing service contract doc: ${d#$ROOT_DIR/}/README.md"
done
pass "Service directory structure exists"

service_entries=(
  "$ROOT_DIR/services/orchestrator/src/index.js"
  "$ROOT_DIR/services/mcp-gateway/src/index.js"
  "$ROOT_DIR/services/approval-gateway/src/index.js"
  "$ROOT_DIR/services/executor/src/index.js"
  "$ROOT_DIR/services/agents/code/src/index.js"
  "$ROOT_DIR/services/agents/email/src/index.js"
  "$ROOT_DIR/services/agents/calendar/src/index.js"
  "$ROOT_DIR/services/agents/linear/src/index.js"
  "$ROOT_DIR/services/agents/slack/src/index.js"
  "$ROOT_DIR/services/agents/todo/src/index.js"
)

for f in "${service_entries[@]}"; do
  [ -f "$f" ] || fail "Missing service entrypoint: ${f#$ROOT_DIR/}"
done
pass "Service entrypoints exist"

bash -n "$ROOT_DIR/scripts"/*.sh "$ROOT_DIR/homelab/scripts"/*.sh
pass "Shell scripts parse"

pass "Repository validation complete"

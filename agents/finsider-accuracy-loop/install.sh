#!/bin/bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPO_ROOT="$(cd "$SOURCE_DIR/../.." && pwd -P)"
CANONICAL_SOURCE="/Users/dm3n/lab/homelab-macintosh/agents/finsider-accuracy-loop"
RUNTIME_DIR="${FINSIDER_ACCURACY_RUNTIME:-/Users/dm3n/finsider-platform/.accuracy-supervisor}"
LAUNCH_AGENTS_DIR="${FINSIDER_LAUNCH_AGENTS_DIR:-/Users/dm3n/Library/LaunchAgents}"
LOG_DIR="${FINSIDER_LOG_DIR:-/Users/dm3n/Library/Logs/Finsider}"
PLIST_SOURCE="$SOURCE_DIR/com.finsider.accuracy-loop.plist"
PLIST_TARGET="$LAUNCH_AGENTS_DIR/com.finsider.accuracy-loop.plist"
DOMAIN="gui/$(id -u)"
LEGACY_PATTERN='/Users/dm3n/finsider-platform/.accuracy-fix-loop/run-iteration.sh|/Users/dm3n/.claude/scripts/tieout-loop/agent.py'

usage() {
  echo "Usage: $0 --check | --activate"
}

preflight() {
  local command_name
  for command_name in python3 claude git gh plutil launchctl pgrep; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      echo "missing required command: $command_name" >&2
      return 2
    fi
  done
  test -f "$SOURCE_DIR/run.py"
  test -f "$SOURCE_DIR/contract.md"
  test -f "$SOURCE_DIR/prompts/spec.md"
  test -f "$SOURCE_DIR/prompts/build.md"
  test -f "$SOURCE_DIR/prompts/judge.md"
  plutil -lint "$PLIST_SOURCE" >/dev/null
  PYTHONPATH="$SOURCE_DIR" python3 -m py_compile \
    "$SOURCE_DIR/run.py" \
    "$SOURCE_DIR/accuracy_loop/model.py" \
    "$SOURCE_DIR/accuracy_loop/claude.py" \
    "$SOURCE_DIR/accuracy_loop/guard.py" \
    "$SOURCE_DIR/accuracy_loop/safe_tools.py" \
    "$SOURCE_DIR/accuracy_loop/workspace.py" \
    "$SOURCE_DIR/accuracy_loop/supervisor.py"
}

legacy_processes_running() {
  pgrep -f "$LEGACY_PATTERN" >/dev/null 2>&1
}

supervisor_process_running() {
  pgrep -f "$CANONICAL_SOURCE/run.py" >/dev/null 2>&1
}

full_validation() {
  PYTHONPATH="$SOURCE_DIR" /usr/bin/python3 -W error::ResourceWarning -m unittest \
    discover -s "$SOURCE_DIR/tests" -v
  make -C "$REPO_ROOT" validate
}

activate() {
  local backup_dir had_previous
  preflight
  if legacy_processes_running; then
    echo "legacy accuracy process is still active; wait for its current iteration to finish" >&2
    return 3
  fi
  if [[ "$SOURCE_DIR" != "$CANONICAL_SOURCE" ]]; then
    echo "activation must run from canonical source: $CANONICAL_SOURCE" >&2
    return 4
  fi
  full_validation

  backup_dir="$(mktemp -d)"
  had_previous=0
  if [[ -f "$PLIST_TARGET" ]]; then
    cp "$PLIST_TARGET" "$backup_dir/previous.plist"
    had_previous=1
  fi

  if supervisor_process_running; then
    launchctl kill SIGTERM "$DOMAIN/com.finsider.accuracy-loop" >/dev/null 2>&1 || true
    for _ in {1..30}; do
      if ! supervisor_process_running; then
        break
      fi
      sleep 1
    done
    if supervisor_process_running; then
      echo "running supervisor did not stop cleanly; activation aborted" >&2
      rm -rf "$backup_dir"
      return 6
    fi
  fi

  launchctl bootout "$DOMAIN/com.finsider.accuracy-loop" >/dev/null 2>&1 || true
  launchctl bootout "$DOMAIN/com.finsider.tieout-loop" >/dev/null 2>&1 || true

  if ! mkdir -p "$RUNTIME_DIR" "$LAUNCH_AGENTS_DIR" "$LOG_DIR" || \
     ! FINSIDER_ACCURACY_RUNTIME="$RUNTIME_DIR" PYTHONPATH="$SOURCE_DIR" \
       /usr/bin/python3 -c \
       'import os; from accuracy_loop.supervisor import Supervisor; Supervisor(os.environ["FINSIDER_ACCURACY_RUNTIME"], os.environ["PYTHONPATH"]).ensure_runtime()' || \
     ! install -m 644 "$PLIST_SOURCE" "$PLIST_TARGET" || \
     ! launchctl bootstrap "$DOMAIN" "$PLIST_TARGET" || \
     ! launchctl enable "$DOMAIN/com.finsider.accuracy-loop" || \
     ! launchctl print "$DOMAIN/com.finsider.accuracy-loop" >/dev/null; then
    echo "activation failed; restoring previous launchd configuration" >&2
    launchctl bootout "$DOMAIN/com.finsider.accuracy-loop" >/dev/null 2>&1 || true
    if [[ "$had_previous" -eq 1 ]]; then
      cp "$backup_dir/previous.plist" "$PLIST_TARGET"
      launchctl bootstrap "$DOMAIN" "$PLIST_TARGET" >/dev/null 2>&1 || true
    else
      rm -f "$PLIST_TARGET"
    fi
    rm -rf "$backup_dir"
    return 5
  fi
  for _ in {1..15}; do
    if supervisor_process_running; then
      break
    fi
    sleep 1
  done
  if ! supervisor_process_running; then
    echo "supervisor was loaded but no running PID was observed" >&2
    launchctl bootout "$DOMAIN/com.finsider.accuracy-loop" >/dev/null 2>&1 || true
    if [[ "$had_previous" -eq 1 ]]; then
      cp "$backup_dir/previous.plist" "$PLIST_TARGET"
      launchctl bootstrap "$DOMAIN" "$PLIST_TARGET" >/dev/null 2>&1 || true
    else
      rm -f "$PLIST_TARGET"
    fi
    rm -rf "$backup_dir"
    return 7
  fi
  rm -rf "$backup_dir"
  echo "continuous Finsider accuracy supervisor activated"
}

case "${1:-}" in
  --check)
    preflight
    if legacy_processes_running; then
      echo "preflight passed; a legacy accuracy process is still active"
    else
      echo "preflight passed"
    fi
    ;;
  --activate)
    activate
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

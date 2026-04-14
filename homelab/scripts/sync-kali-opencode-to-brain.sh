#!/usr/bin/env bash
set -euo pipefail

BRAIN_ROOT="${BRAIN_ROOT:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain}"
OUT_DIR="${OUT_DIR:-$BRAIN_ROOT/Raw/Conversations/Kali OpenCode}"
STATE_DIR="${STATE_DIR:-$HOME/lab/homelab-macintosh/homelab/.state}"
STATE_FILE="${STATE_FILE:-$STATE_DIR/kali-opencode-synced-sessions.txt}"
KALI_HOST="${KALI_HOST:-kali}"

mkdir -p "$OUT_DIR" "$STATE_DIR"
touch "$STATE_FILE"

tmp_ids="$(mktemp)"
tmp_raw="$(mktemp)"
tmp_json="$(mktemp)"
trap 'rm -f "$tmp_ids" "$tmp_raw" "$tmp_json"' EXIT

ssh -o BatchMode=yes "$KALI_HOST" \
  "opencode session list | awk '/^ses_/ {print \$1}'" > "$tmp_ids"

while IFS= read -r session_id; do
  [[ -z "$session_id" ]] && continue

  if grep -Fqx "$session_id" "$STATE_FILE"; then
    continue
  fi

  if ! ssh -o BatchMode=yes "$KALI_HOST" "opencode export $session_id" > "$tmp_raw" 2>/dev/null; then
    continue
  fi

  awk 'BEGIN{emit=0} /^\{/ {emit=1} emit {print}' "$tmp_raw" > "$tmp_json"
  if [[ ! -s "$tmp_json" ]]; then
    continue
  fi

  # Skip malformed/incomplete exports instead of aborting the whole sync loop.
  if ! jq empty "$tmp_json" >/dev/null 2>&1; then
    continue
  fi

  created_ms="$(jq -r '.info.time.created // 0' "$tmp_json")"
  updated_ms="$(jq -r '.info.time.updated // 0' "$tmp_json")"
  title="$(jq -r '.info.title // "Untitled Session"' "$tmp_json" | tr '\n' ' ' | sed 's/  */ /g')"
  model_ids="$(jq -r '[.messages[].info.model.modelID? // .messages[].info.modelID?] | map(select(. != null and . != "")) | unique | join(", ")' "$tmp_json")"
  user_prompts="$(jq -r '[.messages[] | select(.info.role=="user") | .parts[]?.text] | .[:6] | map("- " + .) | join("\n")' "$tmp_json")"

  created_iso="$(date -r $((created_ms / 1000)) +"%Y-%m-%dT%H:%M:%S%z" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")"
  updated_iso="$(date -r $((updated_ms / 1000)) +"%Y-%m-%dT%H:%M:%S%z" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S%z")"
  stamp="$(date -r $((updated_ms / 1000)) +"%Y-%m-%d_%H-%M-%S" 2>/dev/null || date +"%Y-%m-%d_%H-%M-%S")"

  out_file="$OUT_DIR/${stamp}_${session_id}.md"
  {
    echo "---"
    echo "source: kali-opencode"
    echo "session_id: $session_id"
    echo "created: $created_iso"
    echo "updated: $updated_iso"
    echo "title: \"$title\""
    echo "models: \"$model_ids\""
    echo "---"
    echo
    echo "# Kali OpenCode Session"
    echo
    echo "## User Prompts"
    if [[ -n "$user_prompts" ]]; then
      echo "$user_prompts"
    else
      echo "- (none captured)"
    fi
    echo
    echo "## Export JSON"
    echo
    echo '```json'
    cat "$tmp_json"
    echo '```'
  } > "$out_file"

  echo "$session_id" >> "$STATE_FILE"
  echo "Synced $session_id -> $out_file"
done < "$tmp_ids"

echo "Done. Synced session count: $(wc -l < "$STATE_FILE" | tr -d ' ')"

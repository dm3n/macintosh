#!/usr/bin/env python3
"""Claude PreToolUse guard for non-negotiable accuracy-loop safety rails."""

import json
import os
import re
import sys


READ_ONLY_PATTERNS = (
    r"\bgit\s+(?:add|commit|push|merge|rebase|reset|clean|checkout|switch)\b",
    r"\bgit\s+worktree\s+(?:add|remove|move|prune)\b",
    r"\bgh\s+pr\s+(?:create|merge|close|edit|ready|comment|review)\b",
    r"\bgh\s+issue\s+(?:create|edit|close|comment)\b",
    r"\b(?:rm|mv|cp|mkdir|touch|chmod|chown|tee)\b",
    r"\bsed\s+-i\b",
)

UNIVERSAL_DENY_PATTERNS = (
    r"\bgh\s+pr\s+(?:merge|close)\b",
    r"\bgh\s+release\s+(?:create|delete|upload)\b",
    r"\bgh\s+api\b.*(?:-X|--method)\s*(?:POST|PUT|PATCH|DELETE)\b",
    r"\bgh\s+api\b.*(?:-f|--field|-F|--raw-field|--input)\b",
    r"\bgit\s+push\b.*(?:--force(?:-with-lease)?|-f\b)",
    r"\bgit\s+push\b.*(?:\bmain\b|\bmaster\b|\bdevelopment\b)",
    r"\bvercel\b.*(?:\bdeploy\b|--prod\b)",
    r"\baz\b.*\b(?:deploy|deployment)\b",
    r"\baz\s+rest\b.*--method\s*(?:post|put|patch|delete)\b",
    r"\bgcloud\b.*\bdeploy\b",
    r"\bkubectl\s+(?:apply|delete|replace|patch|rollout)\b",
    r"\b(?:terraform|tofu)\s+apply\b",
    r"\b(?:npm|pnpm|yarn)\s+publish\b",
    r"\bdocker\s+push\b",
    r"\bcurl\b.*(?:-X|--request)\s*(?:POST|PUT|PATCH|DELETE)\b",
    r"\bcurl\b.*(?:--data(?:-binary|-raw|-urlencode)?|-d\b|--form|-F\b)",
    r"\bpsql\b.*\b(?:INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b",
    r"\bredis-cli\b.*\b(?:SET|DEL|FLUSHALL|FLUSHDB|UNLINK|RENAME)\b",
)


def _matches(patterns, command):
    return next((pattern for pattern in patterns if re.search(pattern, command, re.IGNORECASE)), None)


def blocked_reason(phase, command):
    command_without_dev_null = re.sub(r"\d?>\s*/dev/null", "", command)
    universal = _matches(UNIVERSAL_DENY_PATTERNS, command_without_dev_null)
    if universal:
        return "command can merge, deploy, publish, force-push, or mutate external data"
    if phase in ("spec", "judge"):
        read_only = _matches(READ_ONLY_PATTERNS, command_without_dev_null)
        if read_only:
            return "%s phase is read-only" % phase
        if re.search(r"(?:^|\s)(?:>>?|1>|2>)\s*\S+", command_without_dev_null):
            return "%s phase cannot redirect output to a file" % phase
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        print("blocked by Finsider accuracy safety rail: malformed hook input", file=sys.stderr)
        return 2
    if payload.get("tool_name") != "Bash":
        return 0
    command = payload.get("tool_input", {}).get("command", "")
    phase = os.environ.get("FINSIDER_ACCURACY_PHASE", "unknown")
    reason = blocked_reason(phase, command)
    if reason:
        print("blocked by Finsider accuracy safety rail: %s" % reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

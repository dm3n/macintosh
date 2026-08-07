#!/usr/bin/env python3
"""Claude PreToolUse guard for non-negotiable accuracy-loop safety rails."""

import json
import os
import re
import sys


DELIVERY_ROOT = "/Users/dm3n/finsider-platform/.accuracy-supervisor/worktrees"
FORBIDDEN_EDIT_PATHS = (
    re.compile(r"^\.git(?:/|$)"),
    re.compile(r"^\.github/(?:workflows|actions)/"),
    re.compile(r"^\.circleci/"),
    re.compile(r"^(?:azure-pipelines|vercel|netlify)\.(?:yml|yaml|json|toml)$"),
    re.compile(r"^(?:Dockerfile|docker-compose(?:\.[^.]+)?\.ya?ml)$"),
    re.compile(r"^(?:infra|infrastructure|terraform|kubernetes|k8s|deploy)/"),
    re.compile(r"^scripts/.*(?:deploy|release|publish)"),
)

READ_ONLY_PATTERNS = (
    r"\bgit(?:\s+-C\s+\S+)?\s+(?:add|commit|push|merge|rebase|reset|clean|checkout|switch)\b",
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
    r"\bgit(?:\s+-C\s+\S+)?\s+push\b.*(?:--force(?:-with-lease)?|-f\b)",
    r"\bgit(?:\s+-C\s+\S+)?\s+push\b.*(?:\bmain\b|\bmaster\b|\bdevelopment\b)",
    r"\bvercel\b.*(?:\bdeploy\b|--prod\b)",
    r"\baz\b.*\b(?:deploy|deployment)\b",
    r"\baz\s+rest\b.*--method\s*(?:post|put|patch|delete)\b",
    r"\bgcloud\b.*\bdeploy\b",
    r"\bkubectl\s+(?:apply|delete|replace|patch|rollout)\b",
    r"\b(?:terraform|tofu)\s+apply\b",
    r"\b(?:npm|pnpm|yarn)\s+publish\b",
    r"\bdocker\s+push\b",
    r"\bcurl\b",
    r"\bpsql\b.*\b(?:INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b",
    r"\bredis-cli\b.*\b(?:SET|DEL|FLUSHALL|FLUSHDB|UNLINK|RENAME)\b",
    r"\b(?:bash|sh|zsh)\s+-c\b",
    r"\bpython(?:3(?:\.\d+)?)?\s+-c\b",
    r"\b(?:eval|source)\b",
    r"[`]|\$\(",
    r"[;|]",
)

READ_BUILTIN_TOOLS = {
    "Read", "Glob", "Grep", "WebFetch", "WebSearch", "StructuredOutput",
}
BUILD_BUILTIN_TOOLS = READ_BUILTIN_TOOLS | {"Edit", "Write", "NotebookEdit"}
VERIFICATION_READ_TOOLS = {
    "mcp__finsider-verification__list_workspaces",
    "mcp__finsider-verification__get_verification_run",
    "mcp__finsider-verification__get_reconciliation_summary",
    "mcp__finsider-verification__get_discrepancies",
    "mcp__finsider-verification__get_balance_sheet_checks",
    "mcp__finsider-verification__get_pnl_identities",
}
VERIFICATION_BUILD_TOOLS = VERIFICATION_READ_TOOLS | {
    "mcp__finsider-verification__trigger_verification_run",
    "mcp__finsider-verification__reconcile_deletions",
}
SAFE_READ_TOOLS = {
    "mcp__finsider-accuracy-tools__inspect_repo",
    "mcp__finsider-accuracy-tools__run_test",
    "mcp__finsider-accuracy-tools__compute_roster_snapshot",
}
SAFE_DELIVERY_TOOLS = SAFE_READ_TOOLS | {
    "mcp__finsider-accuracy-tools__commit_changes",
    "mcp__finsider-accuracy-tools__push_branch",
    "mcp__finsider-accuracy-tools__create_or_view_pr",
}


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


def tool_blocked_reason(phase, tool_name, tool_input):
    if tool_name == "Bash":
        return "general shell execution is disabled; use finsider-accuracy-tools"
    builtins = BUILD_BUILTIN_TOOLS if phase in ("code", "rework") else READ_BUILTIN_TOOLS
    if tool_name in ("Edit", "Write", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path")
        if not isinstance(path, str) or not path:
            return "edit tool did not provide a file path"
        resolved = os.path.realpath(path if os.path.isabs(path) else os.path.join(os.getcwd(), path))
        active_worktree = os.environ.get("FINSIDER_ACCURACY_WORKTREE")
        if not active_worktree:
            return "active persisted worktree was not supplied to the edit guard"
        worktree_root = os.path.realpath(active_worktree)
        delivery_root = os.path.realpath(DELIVERY_ROOT)
        if not worktree_root.startswith(delivery_root + os.sep):
            return "active worktree is outside the persisted delivery root"
        if resolved != worktree_root and not resolved.startswith(worktree_root + os.sep):
            return "edits are restricted to the active persisted accuracy worktree"
        worktree_relative = os.path.relpath(resolved, worktree_root).replace(os.sep, "/")
        if any(pattern.search(worktree_relative) for pattern in FORBIDDEN_EDIT_PATHS):
            return "workflow, deployment, and infrastructure paths are read-only"
    if tool_name in builtins:
        return None
    if not tool_name.startswith("mcp__"):
        return "tool is outside the phase allowlist"
    if phase in ("spec", "judge"):
        if tool_name in SAFE_READ_TOOLS:
            return None
        if tool_name in VERIFICATION_READ_TOOLS:
            return None
        return "%s phase permits only read-only verification MCP tools" % phase
    if phase == "proof":
        if tool_name in SAFE_READ_TOOLS or tool_name in VERIFICATION_BUILD_TOOLS:
            if (
                tool_name == "mcp__finsider-verification__reconcile_deletions"
                and tool_input.get("apply") is not False
            ):
                return "deletion reconciliation must explicitly use apply=false"
            return None
        return "proof phase permits only safe verification and inspection tools"
    if phase in ("code", "rework") and tool_name in SAFE_DELIVERY_TOOLS:
        return None
    if phase == "operations" and tool_name in VERIFICATION_READ_TOOLS:
        return None
    if tool_name in VERIFICATION_BUILD_TOOLS:
        if (
            tool_name == "mcp__finsider-verification__reconcile_deletions"
            and tool_input.get("apply") is not False
        ):
            return "deletion reconciliation must explicitly use apply=false"
        return None
    lowered = tool_name.lower()
    if phase == "operations" and lowered.startswith("mcp__atlassian__"):
        if any(token in lowered for token in ("delete", "remove", "archive", "admin")):
            return "destructive Atlassian action is not allowed"
        if any(token in lowered for token in (
            "search", "get", "list", "createissue", "create_issue", "updateissue",
            "update_issue", "comment", "transitionissue", "transition_issue",
        )):
            return None
    return "MCP tool is outside the build-phase allowlist"


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        print("blocked by Finsider accuracy safety rail: malformed hook input", file=sys.stderr)
        return 2
    phase = os.environ.get("FINSIDER_ACCURACY_PHASE", "unknown")
    reason = tool_blocked_reason(
        phase, payload.get("tool_name", ""), payload.get("tool_input", {})
    )
    if reason:
        print("blocked by Finsider accuracy safety rail: %s" % reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

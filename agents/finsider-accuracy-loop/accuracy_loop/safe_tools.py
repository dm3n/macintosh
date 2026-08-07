#!/usr/bin/env python3
"""Narrow MCP command service for the continuous accuracy loop."""

import json
import os
import re
import subprocess
import sys


ALLOWED_ROOTS = (
    "/Users/dm3n/finsider-platform",
    "/Users/dm3n/finsider-platform/.accuracy-supervisor/worktrees",
)
ALLOWED_BASES = {
    "Mitch-be": "development",
    "Mitch-fe": "development",
    "AI-Agents-CFO": "main",
    "finsider-excel-agent": "main",
    "finsider-mcp": "main",
    "finsider-agents": "main",
}
ALLOWED_NPX = {"eslint", "jest", "playwright", "tsc", "vitest"}
ALLOWED_SCRIPTS = {"check", "lint", "test", "test:unit", "typecheck", "type-check", "tsc"}
PLAIN_ENGLISH_FIELDS = (
    "**What changed.**",
    "**Who it affects.**",
    "**Does a reported number move?**",
    "**What Mitch must do.**",
    "**How to check it in two minutes.**",
    "**If this is wrong.**",
)


def _cwd():
    cwd = os.path.realpath(os.getcwd())
    if not any(cwd == root or cwd.startswith(root + os.sep) for root in ALLOWED_ROOTS):
        raise ValueError("working directory is outside the Finsider allowlist")
    return cwd


def _run(command, cwd=None, environment=None, timeout=1800):
    result = subprocess.run(
        command,
        cwd=cwd or _cwd(),
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    output = ((result.stdout or "") + ("\n" + result.stderr if result.stderr else "")).strip()
    if result.returncode != 0:
        raise RuntimeError("command exited %s: %s" % (result.returncode, output[-4000:]))
    return output[-12000:]


def _branch(cwd):
    branch = _run(["git", "branch", "--show-current"], cwd=cwd, timeout=30).strip()
    if not branch.startswith("agent/accuracy-"):
        raise ValueError("delivery tool requires an agent/accuracy-* branch")
    return branch


def _safe_test_environment():
    allowed = ("PATH", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "TERM")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update({
        "HOME": "/var/empty",
        "XDG_CONFIG_HOME": "/var/empty",
        "FNM_DIR": "/Users/dm3n/.local/share/fnm",
        "FNM_VERSION_FILE_STRATEGY": "local",
        "NPM_CONFIG_USERCONFIG": "/dev/null",
        "NPM_CONFIG_CACHE": "/tmp/finsider-accuracy-npm-cache",
        "CI": "true",
    })
    return environment


def _validated_test_command(runner, args):
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ValueError("test args must be strings")
    if runner == "fnm":
        if len(args) < 4 or args[:2] != ["exec", "--using=20"]:
            raise ValueError("fnm tests must use: exec --using=20 <runner> ...")
        return ["fnm"] + args[:2] + _validated_test_command(args[2], args[3:])
    if runner in ("npm", "pnpm", "yarn"):
        if not args:
            raise ValueError("package runner requires a test command")
        if args[0] == "test":
            return [runner] + args
        if len(args) >= 2 and args[0] == "run" and args[1] in ALLOWED_SCRIPTS:
            return [runner] + args
        if len(args) >= 2 and args[0] in ("exec", "dlx") and args[1] in ALLOWED_NPX:
            return [runner] + args
        raise ValueError("package runner permits only test, lint, typecheck, or approved tools")
    if runner == "npx":
        if not args or args[0] not in ALLOWED_NPX:
            raise ValueError("npx tool is not allowlisted")
        return [runner] + args
    if runner == "node":
        if not args or args[0] != "--test":
            raise ValueError("node permits only the built-in test runner")
        return [runner] + args
    if runner == "python3":
        if len(args) < 2 or args[0] != "-m" or args[1] not in (
            "compileall", "py_compile", "pytest", "unittest",
        ):
            raise ValueError("python permits only approved test or compile modules")
        return ["/usr/bin/python3"] + args
    raise ValueError("test runner is not allowlisted")


def inspect_repo(arguments):
    cwd = _cwd()
    operation = arguments.get("operation")
    if operation == "status":
        return _run(["git", "status", "--short", "--branch"], cwd=cwd, timeout=30)
    if operation == "diff":
        ref = arguments.get("ref") or "HEAD"
        if not re.fullmatch(r"[A-Za-z0-9_./@:{},=+~-]+", ref):
            raise ValueError("diff ref is invalid")
        return _run(["git", "diff", "--stat", ref], cwd=cwd, timeout=60)
    if operation == "log":
        return _run(["git", "log", "-20", "--oneline", "--decorate"], cwd=cwd, timeout=30)
    if operation == "show":
        ref = arguments.get("ref") or "HEAD"
        if not re.fullmatch(r"[A-Za-z0-9_./@:{},=+~-]+", ref):
            raise ValueError("show ref is invalid")
        return _run(["git", "show", "--stat", "--oneline", ref], cwd=cwd, timeout=60)
    raise ValueError("unknown read-only Git operation")


def run_test(arguments):
    command = _validated_test_command(arguments.get("runner"), arguments.get("args", []))
    timeout = arguments.get("timeout_seconds", 1800)
    if type(timeout) is not int or timeout < 1 or timeout > 3600:
        raise ValueError("timeout_seconds must be between 1 and 3600")
    return _run(command, environment=_safe_test_environment(), timeout=timeout)


def commit_changes(arguments):
    cwd = _cwd()
    _branch(cwd)
    message = arguments.get("message", "")
    if not isinstance(message, str) or not re.fullmatch(r"[a-z]+(?:\([^)]+\))?: .{3,120}", message):
        raise ValueError("commit message must use a concise conventional-commit subject")
    if re.search(r"co-authored-by|claude|codex|generated by|\bai\b", message, re.IGNORECASE):
        raise ValueError("AI attribution is forbidden")
    environment = _safe_test_environment()
    _run(["git", "add", "--all"], cwd=cwd, environment=environment, timeout=60)
    return _run([
        "git", "-c", "user.name=Daniel Edgar", "-c", "user.email=daniel@nodebase.ca",
        "-c", "core.hooksPath=/dev/null", "commit", "--no-verify", "-m", message,
    ], cwd=cwd, environment=environment, timeout=120)


def push_branch(_arguments):
    cwd = _cwd()
    branch = _branch(cwd)
    if _run(["git", "status", "--porcelain"], cwd=cwd, timeout=30):
        raise ValueError("worktree must be clean before push")
    return _run(
        ["git", "push", "--set-upstream", "origin", "HEAD:refs/heads/%s" % branch],
        cwd=cwd,
        timeout=300,
    )


def _repository_name(cwd):
    remote = _run(["git", "remote", "get-url", "origin"], cwd=cwd, timeout=30)
    name = remote.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    if name not in ALLOWED_BASES:
        raise ValueError("repository remote is not allowlisted")
    return name


def create_or_view_pr(arguments):
    cwd = _cwd()
    branch = _branch(cwd)
    repository = _repository_name(cwd)
    base = arguments.get("base")
    title = arguments.get("title", "")
    body = arguments.get("body", "")
    moves_numbers = arguments.get("moves_customer_numbers")
    if base != ALLOWED_BASES[repository]:
        raise ValueError("PR base does not match the repository contract")
    if type(moves_numbers) is not bool:
        raise ValueError("moves_customer_numbers must be boolean")
    if moves_numbers and "NEEDS CPA REVIEW" not in title:
        raise ValueError("number-moving PR title must contain NEEDS CPA REVIEW")
    if any(field not in body for field in PLAIN_ENGLISH_FIELDS):
        raise ValueError("PR body is missing the six-field Plain English block")
    if re.search(r"co-authored-by|generated by (?:claude|codex)|\bai attribution\b", body, re.I):
        raise ValueError("AI attribution is forbidden")
    existing = _run(
        ["gh", "pr", "list", "--head", branch, "--state", "all", "--json", "url,state,title"],
        cwd=cwd,
        timeout=60,
    )
    pulls = json.loads(existing or "[]")
    if pulls:
        return json.dumps({"reused": True, "pull_request": pulls[0]}, sort_keys=True)
    created = _run(
        [
            "gh", "pr", "create", "--base", base, "--head", branch, "--title", title,
            "--body", body,
        ],
        cwd=cwd,
        timeout=120,
    )
    return json.dumps({"reused": False, "url": created.strip()}, sort_keys=True)


TOOL_HANDLERS = {
    "inspect_repo": inspect_repo,
    "run_test": run_test,
    "commit_changes": commit_changes,
    "push_branch": push_branch,
    "create_or_view_pr": create_or_view_pr,
}

TOOLS = [
    {
        "name": "inspect_repo",
        "description": "Read Git status, diff summary, log, or commit summary in the current Finsider checkout.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {"enum": ["status", "diff", "log", "show"]},
                "ref": {"type": "string"},
            },
            "required": ["operation"],
        },
    },
    {
        "name": "run_test",
        "description": "Run one allowlisted local test, lint, typecheck, or compile command with credentials removed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "runner": {"enum": ["fnm", "npm", "pnpm", "yarn", "npx", "node", "python3"]},
                "args": {"type": "array", "items": {"type": "string"}},
                "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
            },
            "required": ["runner", "args"],
        },
    },
    {
        "name": "commit_changes",
        "description": "Commit the current isolated accuracy worktree as Daniel with a validated message.",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
    {
        "name": "push_branch",
        "description": "Push the current clean agent/accuracy branch without force to the same remote branch.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "create_or_view_pr",
        "description": "Reuse or create one PR from the current accuracy branch with exact base and safety labels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base": {"enum": ["main", "development"]},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "moves_customer_numbers": {"type": "boolean"},
            },
            "required": ["base", "title", "body", "moves_customer_numbers"],
        },
    },
]


def _response(request_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = {"code": -32000, "message": str(error)}
    else:
        payload["result"] = result
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            request_id = request.get("id")
            if method == "initialize":
                _response(request_id, {
                    "protocolVersion": request.get("params", {}).get(
                        "protocolVersion", "2024-11-05"
                    ),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "finsider-accuracy-tools", "version": "1.0.0"},
                })
            elif method == "tools/list":
                _response(request_id, {"tools": TOOLS})
            elif method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                if name not in TOOL_HANDLERS:
                    raise ValueError("unknown tool")
                output = TOOL_HANDLERS[name](params.get("arguments", {}))
                _response(request_id, {
                    "content": [{"type": "text", "text": output or "ok"}],
                    "isError": False,
                })
            elif request_id is not None:
                _response(request_id, {})
        except Exception as error:
            if "request_id" in locals() and request_id is not None:
                _response(request_id, error=error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

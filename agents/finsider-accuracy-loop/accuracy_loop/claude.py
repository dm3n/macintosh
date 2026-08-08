"""Run one fresh, structured Claude Code context for each loop phase."""

import json
import os
import signal
import subprocess
import uuid
from datetime import datetime, timezone


CLAUDE_BIN = "/opt/homebrew/bin/claude"
MODEL = "claude-sonnet-4-6"
GUARD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard.py")
SAFE_TOOLS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safe_tools.py")
VERIFICATION_MCP_PATH = "/Users/dm3n/finsider-platform/verification-mcp/index.mjs"

PRODUCTION_MUTATION_TOOLS = (
    "mcp__finsider-verification__review_discrepancy",
    "mcp__finsider-verification__remove_all_discrepancies",
    "mcp__finsider-verification__reconcile_deletions",
)
VERIFICATION_READ_TOOLS = (
    "mcp__finsider-verification__list_workspaces",
    "mcp__finsider-verification__get_verification_run",
    "mcp__finsider-verification__get_reconciliation_summary",
    "mcp__finsider-verification__get_discrepancies",
    "mcp__finsider-verification__get_balance_sheet_checks",
    "mcp__finsider-verification__get_pnl_identities",
)
VERIFICATION_BUILD_TOOLS = VERIFICATION_READ_TOOLS + (
    "mcp__finsider-verification__trigger_verification_run",
    "mcp__finsider-verification__reconcile_deletions",
)
READ_BUILTINS = ("Read", "Glob", "Grep", "WebFetch", "WebSearch", "StructuredOutput")
BUILD_BUILTINS = READ_BUILTINS + ("Edit", "Write", "NotebookEdit")
READ_ONLY_PHASE_TOOLS = ("Edit", "Write", "NotebookEdit", "Agent") + PRODUCTION_MUTATION_TOOLS
BUILD_PHASE_TOOLS = ("Agent",) + PRODUCTION_MUTATION_TOOLS

SENSITIVE_ENV_FRAGMENTS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "DATABASE_URL",
    "VERCEL_TOKEN",
    "AZURE_",
    "SUPABASE_",
    "RAILZ_",
    "CLERK_SECRET",
    "STRIPE_",
    "MEOW_",
    "AWS_SECRET",
    "AWS_ACCESS",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "SLACK_BOT_TOKEN",
    "REDIS_URL",
)

SAFE_READ_TOOLS = (
    "mcp__finsider-accuracy-tools__inspect_repo",
    "mcp__finsider-accuracy-tools__run_test",
    "mcp__finsider-accuracy-tools__compute_roster_snapshot",
)
SAFE_DELIVERY_TOOLS = SAFE_READ_TOOLS + (
    "mcp__finsider-accuracy-tools__commit_changes",
    "mcp__finsider-accuracy-tools__push_branch",
    "mcp__finsider-accuracy-tools__create_or_view_pr",
)


class AgentFailure(RuntimeError):
    def __init__(self, message, transient=False):
        super().__init__(message)
        self.transient = transient


def build_command(schema, phase, claude_bin=CLAUDE_BIN):
    if phase in ("code", "rework"):
        disallowed = BUILD_PHASE_TOOLS
        allowed = BUILD_BUILTINS + VERIFICATION_BUILD_TOOLS + SAFE_DELIVERY_TOOLS
        builtins = BUILD_BUILTINS
    elif phase == "proof":
        disallowed = READ_ONLY_PHASE_TOOLS
        allowed = READ_BUILTINS + VERIFICATION_BUILD_TOOLS + SAFE_READ_TOOLS
        builtins = READ_BUILTINS
    elif phase == "operations":
        disallowed = READ_ONLY_PHASE_TOOLS
        allowed = READ_BUILTINS + VERIFICATION_READ_TOOLS + ("mcp__atlassian__*",)
        builtins = READ_BUILTINS
    else:
        disallowed = READ_ONLY_PHASE_TOOLS
        allowed = READ_BUILTINS + VERIFICATION_READ_TOOLS + SAFE_READ_TOOLS
        builtins = READ_BUILTINS
    mcp_config = {
        "mcpServers": {
            "finsider-accuracy-tools": {
                "command": "/usr/bin/python3",
                "args": [SAFE_TOOLS_PATH],
            },
            "finsider-verification": {
                "command": "node",
                "args": [VERIFICATION_MCP_PATH],
            },
            "atlassian": {
                "type": "http",
                "url": "https://mcp.atlassian.com/v1/mcp/authv2",
            },
        }
    }
    settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "/usr/bin/python3 %s" % GUARD_PATH,
                        }
                    ],
                }
            ]
        }
    }
    return [
        claude_bin,
        "-p",
        "--model",
        MODEL,
        "--effort",
        "max",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, separators=(",", ":")),
        "--settings",
        json.dumps(settings, separators=(",", ":")),
        "--mcp-config",
        json.dumps(mcp_config, separators=(",", ":")),
        "--strict-mcp-config",
        "--permission-mode",
        "dontAsk",
        "--tools",
        ",".join(builtins),
        "--allowedTools",
        ",".join(allowed),
        "--disallowedTools",
        ",".join(disallowed),
    ]


def extract_structured_output(raw_output):
    try:
        payload = json.loads(raw_output.strip())
    except (TypeError, ValueError) as error:
        raise AgentFailure("Claude returned malformed JSON: %s" % error) from error
    if not isinstance(payload, dict):
        raise AgentFailure("Claude returned a non-object JSON result")
    structured = payload.get("structured_output")
    if isinstance(structured, dict):
        return structured
    if payload.get("type") == "result":
        raise AgentFailure("Claude result did not contain structured_output")
    return payload


def _is_transient_failure(output):
    lowered = output.lower()
    signals = (
        "rate limit",
        "rate_limit",
        "overloaded",
        "usage limit",
        "capacity",
        "authenticate",
        "authentication",
        "login",
        "oauth",
        "temporarily unavailable",
        "timeout",
        "timed out",
    )
    return any(item in lowered for item in signals)


class ClaudeRunner:
    def __init__(
        self,
        claude_bin=CLAUDE_BIN,
        trace_dir=None,
        timeout_seconds=3600,
        environ=None,
        process_factory=subprocess.Popen,
    ):
        self.claude_bin = claude_bin
        self.trace_dir = trace_dir
        self.timeout_seconds = timeout_seconds
        self.environ = dict(environ if environ is not None else os.environ)
        self.process_factory = process_factory
        self.active_process = None
        self._cancel_requested = False

    def _clean_environment(self, phase):
        environment = {}
        for key, value in self.environ.items():
            upper_key = key.upper()
            if any(fragment in upper_key for fragment in SENSITIVE_ENV_FRAGMENTS):
                continue
            environment[key] = value
        environment["FINSIDER_ACCURACY_PHASE"] = phase
        return environment

    def _trace_paths(self, phase):
        trace_dir = self.trace_dir or os.getcwd()
        os.makedirs(trace_dir, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prefix = "%s-%s-%s" % (stamp, phase, uuid.uuid4().hex[:8])
        return (
            os.path.join(trace_dir, prefix + ".stdout.json"),
            os.path.join(trace_dir, prefix + ".stderr.log"),
        )

    def terminate(self):
        self._cancel_requested = True
        process = self.active_process
        if process is None or process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def run(self, phase, prompt, schema, cwd, capability_phase=None):
        capability_phase = capability_phase or phase
        command = build_command(schema, capability_phase, claude_bin=self.claude_bin)
        stdout_path, stderr_path = self._trace_paths(phase)
        process = None
        self._cancel_requested = False
        try:
            environment = self._clean_environment(capability_phase)
            if capability_phase in ("code", "rework"):
                environment["FINSIDER_ACCURACY_WORKTREE"] = os.path.realpath(cwd)
            process = self.process_factory(
                command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            self.active_process = process
            stdout, stderr = process.communicate(
                input=prompt, timeout=self.timeout_seconds
            )
            return_code = process.returncode
        except subprocess.TimeoutExpired as error:
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            raise AgentFailure(
                "Claude %s phase timed out after %ss" % (phase, self.timeout_seconds),
                transient=True,
            ) from error
        finally:
            if process is not None and self.active_process is process and process.poll() is not None:
                self.active_process = None
            if process is not None and process.poll() is not None:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()

        with open(stdout_path, "w") as stdout_file:
            stdout_file.write(stdout or "")
        with open(stderr_path, "w") as stderr_file:
            stderr_file.write(stderr or "")

        if self._cancel_requested:
            raise AgentFailure("Claude %s phase was interrupted" % phase, transient=True)

        if return_code != 0:
            combined = ((stderr or "") + "\n" + (stdout or "")).strip()
            message = combined[-2000:] if combined else "no process output"
            raise AgentFailure(
                "Claude %s phase exited %s: %s" % (phase, return_code, message),
                transient=_is_transient_failure(combined),
            )
        return extract_structured_output(stdout)

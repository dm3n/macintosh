"""Run one fresh, structured Claude Code context for each loop phase."""

import json
import os
import signal
import subprocess
import uuid
from datetime import datetime, timezone


CLAUDE_BIN = "/opt/homebrew/bin/claude"
MODEL = "claude-sonnet-4-6"

PRODUCTION_MUTATION_TOOLS = (
    "mcp__finsider-verification__review_discrepancy",
    "mcp__finsider-verification__remove_all_discrepancies",
    "mcp__finsider-verification__reconcile_deletions",
)
READ_ONLY_PHASE_TOOLS = ("Edit", "Write", "NotebookEdit", "Agent") + PRODUCTION_MUTATION_TOOLS
BUILD_PHASE_TOOLS = ("Agent",) + PRODUCTION_MUTATION_TOOLS


class AgentFailure(RuntimeError):
    def __init__(self, message, transient=False):
        super().__init__(message)
        self.transient = transient


def build_command(schema, phase, claude_bin=CLAUDE_BIN):
    disallowed = BUILD_PHASE_TOOLS if phase in ("build", "rework") else READ_ONLY_PHASE_TOOLS
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
        "--dangerously-skip-permissions",
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

    def _clean_environment(self):
        return {
            key: value
            for key, value in self.environ.items()
            if key not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
        }

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
        process = self.active_process
        if process is None or process.poll() is not None:
            self.active_process = None
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        finally:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
            self.active_process = None

    def run(self, phase, prompt, schema, cwd):
        command = build_command(schema, phase, claude_bin=self.claude_bin)
        stdout_path, stderr_path = self._trace_paths(phase)
        try:
            self.active_process = self.process_factory(
                command,
                cwd=cwd,
                env=self._clean_environment(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            stdout, stderr = self.active_process.communicate(
                input=prompt, timeout=self.timeout_seconds
            )
            return_code = self.active_process.returncode
        except subprocess.TimeoutExpired as error:
            self.terminate()
            raise AgentFailure(
                "Claude %s phase timed out after %ss" % (phase, self.timeout_seconds),
                transient=True,
            ) from error
        finally:
            if self.active_process is not None and self.active_process.poll() is not None:
                self.active_process = None

        with open(stdout_path, "w") as stdout_file:
            stdout_file.write(stdout or "")
        with open(stderr_path, "w") as stderr_file:
            stderr_file.write(stderr or "")

        if return_code != 0:
            combined = ((stderr or "") + "\n" + (stdout or "")).strip()
            message = combined[-2000:] if combined else "no process output"
            raise AgentFailure(
                "Claude %s phase exited %s: %s" % (phase, return_code, message),
                transient=_is_transient_failure(combined),
            )
        return extract_structured_output(stdout)

import json
import os
import stat
import sys
import tempfile
import textwrap
import threading
import time
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.claude import (  # noqa: E402
    CLAUDE_BIN,
    AgentFailure,
    ClaudeRunner,
    build_command,
    extract_structured_output,
)


SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string"}},
    "required": ["decision"],
}


class ClaudeRunnerTests(unittest.TestCase):
    def test_extracts_structured_output_from_claude_envelope(self):
        raw = json.dumps({"type": "result", "structured_output": {"decision": "code"}})

        self.assertEqual(extract_structured_output(raw), {"decision": "code"})

    def test_extracts_direct_json_object_for_forward_compatibility(self):
        self.assertEqual(extract_structured_output('{"decision":"proof"}'), {"decision": "proof"})

    def test_rejects_missing_structured_output(self):
        with self.assertRaises(AgentFailure) as failure:
            extract_structured_output('{"type":"result","result":"prose only"}')

        self.assertFalse(failure.exception.transient)

    def test_command_uses_fresh_max_effort_subscription_context(self):
        command = build_command(SCHEMA, phase="spec")

        self.assertEqual(command[:4], [CLAUDE_BIN, "-p", "--model", "claude-sonnet-4-6"])
        self.assertIn("--effort", command)
        self.assertEqual(command[command.index("--effort") + 1], "max")
        self.assertIn("--no-session-persistence", command)
        self.assertIn("--output-format", command)
        self.assertIn("--json-schema", command)
        self.assertIn("--settings", command)
        self.assertIn("--disallowedTools", command)
        self.assertIn("--allowedTools", command)
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--mcp-config", command)
        self.assertIn("--permission-mode", command)
        self.assertEqual(command[command.index("--permission-mode") + 1], "dontAsk")
        self.assertNotIn("--dangerously-skip-permissions", command)
        settings = json.loads(command[command.index("--settings") + 1])
        self.assertEqual(settings["hooks"]["PreToolUse"][0]["matcher"], "*")
        self.assertNotIn("Bash", command[command.index("--tools") + 1].split(","))

    def test_code_phase_exposes_only_narrow_delivery_tools(self):
        command = build_command(SCHEMA, phase="code")
        allowed = command[command.index("--allowedTools") + 1].split(",")

        self.assertIn("Edit", allowed)
        self.assertIn("mcp__finsider-accuracy-tools__push_branch", allowed)
        self.assertNotIn("Bash", allowed)
        self.assertNotIn("mcp__vercel__deploy", allowed)

    def test_proof_phase_cannot_edit_or_deliver_code(self):
        command = build_command(SCHEMA, phase="proof")
        allowed = command[command.index("--allowedTools") + 1].split(",")

        self.assertNotIn("Edit", allowed)
        self.assertNotIn("mcp__finsider-accuracy-tools__push_branch", allowed)
        self.assertIn("mcp__finsider-verification__trigger_verification_run", allowed)

    def test_real_child_receives_prompt_without_api_key_and_writes_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_claude = os.path.join(directory, "fake-claude")
            with open(fake_claude, "w") as executable:
                executable.write(textwrap.dedent("""\
                    #!/usr/bin/env python3
                    import json
                    import os
                    import sys
                    prompt = sys.stdin.read()
                    result = {
                        "structured_output": {
                            "decision": "proof" if prompt == "prove it" else "wrong",
                            "api_key_present": "ANTHROPIC_API_KEY" in os.environ,
                            "deploy_token_present": "VERCEL_TOKEN" in os.environ,
                            "database_url_present": "DATABASE_URL" in os.environ,
                        }
                    }
                    print(json.dumps(result))
                """))
            os.chmod(fake_claude, os.stat(fake_claude).st_mode | stat.S_IXUSR)
            traces = os.path.join(directory, "traces")
            env = dict(
                os.environ,
                ANTHROPIC_API_KEY="must-not-leak",
                VERCEL_TOKEN="must-not-leak",
                DATABASE_URL="must-not-leak",
            )
            runner = ClaudeRunner(claude_bin=fake_claude, trace_dir=traces, environ=env)

            result = runner.run("spec", "prove it", SCHEMA, directory)

            self.assertEqual(result["decision"], "proof")
            self.assertFalse(result["api_key_present"])
            self.assertFalse(result["deploy_token_present"])
            self.assertFalse(result["database_url_present"])
            self.assertEqual(len(os.listdir(traces)), 2)

    def test_timeout_is_transient_and_terminates_child(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_claude = os.path.join(directory, "fake-claude")
            with open(fake_claude, "w") as executable:
                executable.write("#!/bin/sh\nsleep 5\n")
            os.chmod(fake_claude, os.stat(fake_claude).st_mode | stat.S_IXUSR)
            runner = ClaudeRunner(claude_bin=fake_claude, trace_dir=directory, timeout_seconds=0.05)

            with self.assertRaises(AgentFailure) as failure:
                runner.run("judge", "input", SCHEMA, directory)

            self.assertTrue(failure.exception.transient)
            self.assertIn("timed out", str(failure.exception))
            self.assertIsNone(runner.active_process)

    def test_concurrent_termination_is_transient_without_process_race(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_claude = os.path.join(directory, "fake-claude")
            with open(fake_claude, "w") as executable:
                executable.write("#!/bin/sh\nsleep 30\n")
            os.chmod(fake_claude, os.stat(fake_claude).st_mode | stat.S_IXUSR)
            runner = ClaudeRunner(claude_bin=fake_claude, trace_dir=directory)
            observed = []

            def invoke():
                try:
                    runner.run("build", "input", SCHEMA, directory)
                except Exception as error:
                    observed.append(error)

            thread = threading.Thread(target=invoke)
            thread.start()
            deadline = time.time() + 5
            while runner.active_process is None and time.time() < deadline:
                time.sleep(0.01)

            runner.terminate()
            thread.join(timeout=5)

            self.assertFalse(thread.is_alive())
            self.assertEqual(len(observed), 1)
            self.assertIsInstance(observed[0], AgentFailure)
            self.assertTrue(observed[0].transient)
            self.assertNotIsInstance(observed[0], AttributeError)
            self.assertIsNone(runner.active_process)


if __name__ == "__main__":
    unittest.main()

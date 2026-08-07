import json
import os
import stat
import sys
import tempfile
import textwrap
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
                        }
                    }
                    print(json.dumps(result))
                """))
            os.chmod(fake_claude, os.stat(fake_claude).st_mode | stat.S_IXUSR)
            traces = os.path.join(directory, "traces")
            env = dict(os.environ, ANTHROPIC_API_KEY="must-not-leak")
            runner = ClaudeRunner(claude_bin=fake_claude, trace_dir=traces, environ=env)

            result = runner.run("spec", "prove it", SCHEMA, directory)

            self.assertEqual(result["decision"], "proof")
            self.assertFalse(result["api_key_present"])
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


if __name__ == "__main__":
    unittest.main()

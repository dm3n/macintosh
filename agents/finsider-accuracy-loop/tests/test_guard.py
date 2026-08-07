import json
import os
import subprocess
import sys
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.guard import blocked_reason, tool_blocked_reason  # noqa: E402


GUARD = os.path.join(PACKAGE_ROOT, "accuracy_loop", "guard.py")


class SafetyGuardTests(unittest.TestCase):
    def test_read_only_phase_blocks_shell_writes_and_external_mutations(self):
        cases = (
            "git commit -m unsafe",
            "printf value > output.txt",
            "gh pr create --title unsafe",
            "curl -X POST https://example.com",
            "rm -f result.json",
        )
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNotNone(blocked_reason("spec", command))
                self.assertIsNotNone(blocked_reason("judge", command))

    def test_read_only_phase_allows_observation_and_tests(self):
        for command in (
            "git diff origin/development...HEAD",
            "gh pr view 1062 --json title,state",
            "rg -n cash_reconciliation src",
            "fnm exec --using=20 npm test -- cash-proof.test.js",
        ):
            with self.subTest(command=command):
                self.assertIsNone(blocked_reason("spec", command))

    def test_build_phase_blocks_merge_deploy_publish_force_and_prod_data_writes(self):
        cases = (
            "gh pr merge 1062 --squash",
            "git push origin main",
            "git push --force origin agent/accuracy-test",
            "vercel deploy --prod",
            "az webapp deploy --name mitch-back",
            "npm publish",
            "curl --request PATCH https://api.example.com/records/1",
            "psql prod -c 'UPDATE report_snapshots SET amount = 0'",
            "git -C /tmp/repo push origin development",
            "curl --json '{\"value\":1}' https://api.example.com/records",
            "bash -c 'vercel deploy --prod'",
            "python3 -c 'import subprocess; subprocess.run([\"vercel\",\"--prod\"])'",
        )
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNotNone(blocked_reason("build", command))

    def test_build_phase_allows_feature_delivery_and_verification(self):
        for command in (
            "git push -u origin agent/accuracy-acc-100-proof-parity",
            "gh pr create --base development --head agent/accuracy-acc-100-proof-parity",
            "fnm exec --using=20 npm test -- verification-run.test.js",
            "git commit -m 'fix: preserve report parity'",
        ):
            with self.subTest(command=command):
                self.assertIsNone(blocked_reason("build", command))

    def test_phase_tool_policy_denies_unknown_and_mutating_mcp_tools(self):
        self.assertIsNone(tool_blocked_reason("spec", "StructuredOutput", {}))
        self.assertIsNotNone(tool_blocked_reason("code", "Bash", {"command": "git status"}))
        self.assertIsNone(tool_blocked_reason("code", "Edit", {
            "file_path": "/Users/dm3n/finsider-platform/.accuracy-supervisor/worktrees/Mitch-be-ACC-1/src/report.js"
        }))
        self.assertIsNotNone(tool_blocked_reason("code", "Edit", {
            "file_path": "/Users/dm3n/finsider-platform/Mitch-be/src/report.js"
        }))
        self.assertIsNotNone(tool_blocked_reason("code", "Write", {
            "file_path": "/Users/dm3n/finsider-platform/.accuracy-supervisor/worktrees/Mitch-be-ACC-1/.github/workflows/deploy.yml"
        }))
        self.assertIsNone(tool_blocked_reason(
            "spec", "mcp__finsider-verification__list_workspaces", {}
        ))
        self.assertIsNotNone(tool_blocked_reason(
            "spec", "mcp__finsider-verification__trigger_verification_run", {}
        ))
        self.assertIsNotNone(tool_blocked_reason(
            "judge", "mcp__vercel__deploy", {"production": True}
        ))
        self.assertIsNotNone(tool_blocked_reason(
            "code", "mcp__finsider-verification__review_discrepancy", {}
        ))
        self.assertIsNotNone(tool_blocked_reason(
            "proof", "mcp__finsider-verification__scan_discrepancies", {}
        ))
        self.assertIsNotNone(tool_blocked_reason(
            "proof", "mcp__finsider-verification__reconcile_deletions", {"apply": True}
        ))
        self.assertIsNone(tool_blocked_reason(
            "proof", "mcp__finsider-verification__reconcile_deletions", {"apply": False}
        ))

    def test_hook_process_denies_with_exit_two(self):
        payload = json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "gh pr merge 1062"},
        })
        environment = dict(os.environ, FINSIDER_ACCURACY_PHASE="code")

        result = subprocess.run(
            [sys.executable, GUARD], input=payload, text=True, capture_output=True, env=environment
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("blocked by Finsider accuracy safety rail", result.stderr)

    def test_hook_process_applies_policy_to_non_bash_tools(self):
        payload = json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__vercel__deploy",
            "tool_input": {"production": True},
        })
        environment = dict(os.environ, FINSIDER_ACCURACY_PHASE="build")

        result = subprocess.run(
            [sys.executable, GUARD], input=payload, text=True, capture_output=True, env=environment
        )

        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.safe_tools import (  # noqa: E402
    _safe_test_environment,
    _delivery_cwd,
    _path_is_forbidden,
    _sandbox_profile,
    _sanitize_test_copy,
    _validated_test_command,
    create_or_view_pr,
    compute_roster_snapshot,
)
from accuracy_loop.model import _workspace_roster_checksum  # noqa: E402


class SafeToolTests(unittest.TestCase):
    def test_test_runner_has_no_shell_and_only_allows_test_commands(self):
        self.assertEqual(
            _validated_test_command("fnm", ["exec", "--using=20", "npm", "test", "--", "cash.test.js"]),
            ["fnm", "exec", "--using=20", "npm", "test", "--", "cash.test.js"],
        )
        for runner, args in (
            ("npm", ["publish"]),
            ("npx", ["vercel", "deploy"]),
            ("python3", ["-c", "import os"]),
            ("node", ["deploy.js"]),
        ):
            with self.subTest(runner=runner):
                with self.assertRaises(ValueError):
                    _validated_test_command(runner, args)

    def test_roster_snapshot_tool_matches_completion_model(self):
        roster = [{
            "workspace_id": "ws1", "name": "Fixture", "lifecycle": "active",
            "included": True, "latest_sync_at": "2026-08-06T20:00:00Z",
            "verification_id": "ignored-by-roster", "verified_at": "2026-08-06T21:00:00Z",
        }]

        result = __import__("json").loads(compute_roster_snapshot({
            "workspace_roster": roster,
            "observed_at": "2026-08-06T22:00:00Z",
        }))

        self.assertEqual(result["checksum"], _workspace_roster_checksum(roster))
        self.assertTrue(result["id"].startswith("roster:%s:" % result["checksum"]))

    def test_test_environment_removes_home_and_production_credentials(self):
        with patch.dict(os.environ, {
            "VERCEL_TOKEN": "secret",
            "DATABASE_URL": "secret",
            "CLERK_SECRET_KEY": "secret",
        }, clear=False):
            environment = _safe_test_environment()

        self.assertEqual(environment["HOME"], "/var/empty")
        self.assertNotIn("VERCEL_TOKEN", environment)
        self.assertNotIn("DATABASE_URL", environment)
        self.assertNotIn("CLERK_SECRET_KEY", environment)

    def test_sandbox_copy_removes_project_secrets_and_git_metadata(self):
        with tempfile.TemporaryDirectory() as source:
            with open(os.path.join(source, "package.json"), "w") as package:
                package.write("{}\n")
            with open(os.path.join(source, ".env.local"), "w") as secret:
                secret.write("SECRET=hidden\n")
            with open(os.path.join(source, ".git"), "w") as git_file:
                git_file.write("gitdir: hidden\n")

            root, copied = _sanitize_test_copy(source)
            try:
                self.assertTrue(os.path.exists(os.path.join(copied, "package.json")))
                self.assertFalse(os.path.exists(os.path.join(copied, ".env.local")))
                self.assertFalse(os.path.exists(os.path.join(copied, ".git")))
            finally:
                shutil.rmtree(root, ignore_errors=True)

    def test_sandbox_denies_network_and_host_profile_reads(self):
        with tempfile.TemporaryDirectory() as test_root, tempfile.TemporaryDirectory() as outside:
            profile = _sandbox_profile(test_root)

            profile_read = subprocess.run([
                "/usr/bin/sandbox-exec", "-p", profile, "--", "/usr/bin/test", "-r",
                os.path.expanduser("~/.config"),
            ], capture_output=True, text=True, check=False)
            network = subprocess.run([
                "/usr/bin/sandbox-exec", "-p", profile, "--", "/usr/bin/curl",
                "--max-time", "1", "https://example.com",
            ], capture_output=True, text=True, check=False)
            host_write = subprocess.run([
                "/usr/bin/sandbox-exec", "-p", profile, "--", "/usr/bin/touch",
                os.path.join(outside, "forbidden"),
            ], capture_output=True, text=True, check=False)

        self.assertIn("(deny network*)", profile)
        self.assertNotEqual(profile_read.returncode, 0)
        self.assertNotEqual(network.returncode, 0)
        self.assertNotEqual(host_write.returncode, 0)

    def test_delivery_paths_and_checkout_are_restricted(self):
        self.assertTrue(_path_is_forbidden(".github/workflows/deploy.yml"))
        self.assertTrue(_path_is_forbidden("infra/production.tf"))
        self.assertFalse(_path_is_forbidden("src/reports/cash-proof.js"))
        with patch("accuracy_loop.safe_tools._cwd", return_value="/Users/dm3n/finsider-platform/Mitch-be"):
            with self.assertRaises(ValueError):
                _delivery_cwd()

    @patch("accuracy_loop.safe_tools._repository_name", return_value="Mitch-be")
    @patch("accuracy_loop.safe_tools._branch", return_value="agent/accuracy-acc-1")
    @patch(
        "accuracy_loop.safe_tools._delivery_cwd",
        return_value="/Users/dm3n/finsider-platform/.accuracy-supervisor/worktrees/Mitch-be-ACC-1",
    )
    def test_pr_tool_requires_cpa_title_and_plain_english_block(
        self, _cwd_mock, _branch_mock, _repo_mock
    ):
        with self.assertRaises(ValueError):
            create_or_view_pr({
                "base": "development",
                "title": "fix cash proof",
                "body": "incomplete",
                "moves_customer_numbers": True,
            })


if __name__ == "__main__":
    unittest.main()

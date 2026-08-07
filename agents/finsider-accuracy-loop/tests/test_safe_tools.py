import os
import sys
import unittest
from unittest.mock import patch


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.safe_tools import (  # noqa: E402
    _safe_test_environment,
    _validated_test_command,
    create_or_view_pr,
)


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

    @patch("accuracy_loop.safe_tools._repository_name", return_value="Mitch-be")
    @patch("accuracy_loop.safe_tools._branch", return_value="agent/accuracy-acc-1")
    @patch("accuracy_loop.safe_tools._cwd", return_value="/Users/dm3n/finsider-platform/Mitch-be")
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

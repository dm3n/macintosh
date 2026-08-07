import os
import subprocess
import sys
import tempfile
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.workspace import (  # noqa: E402
    Repo,
    create_worktree,
    inspect_worktree,
    remove_clean_worktree,
)


def git(*args, cwd):
    return subprocess.run(
        ["git"] + list(args), cwd=cwd, text=True, capture_output=True, check=True
    ).stdout.strip()


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = self.temporary.name
        self.repo = os.path.join(self.root, "repo")
        self.runtime = os.path.join(self.root, "runtime")
        os.makedirs(self.repo)
        git("init", "-b", "development", cwd=self.repo)
        git("config", "user.email", "daniel@nodebase.ca", cwd=self.repo)
        git("config", "user.name", "Daniel Edgar", cwd=self.repo)
        with open(os.path.join(self.repo, "README.md"), "w") as readme:
            readme.write("fixture\n")
        git("add", "README.md", cwd=self.repo)
        git("commit", "-m", "fixture", cwd=self.repo)
        self.repositories = {"fixture": Repo(self.repo, "development")}

    def tearDown(self):
        self.temporary.cleanup()

    def test_rejects_repository_outside_allowlist(self):
        with self.assertRaises(ValueError):
            create_worktree(
                "unknown", "ACC-1", "bad", self.runtime, repositories=self.repositories
            )

    def test_creates_branch_from_configured_base_in_isolated_path(self):
        worktree = create_worktree(
            "fixture",
            "ACC-1",
            "Cash Proof",
            self.runtime,
            repositories=self.repositories,
        )

        self.assertEqual(git("branch", "--show-current", cwd=worktree.path),
                         "agent/accuracy-acc-1-cash-proof")
        self.assertTrue(
            worktree.path.startswith(os.path.realpath(os.path.join(self.runtime, "worktrees")))
        )
        self.assertEqual(worktree.base_branch, "development")

    def test_crash_resume_reuses_matching_worktree(self):
        first = create_worktree(
            "fixture", "ACC-2", "Parity", self.runtime, repositories=self.repositories
        )

        second = create_worktree(
            "fixture", "ACC-2", "Parity", self.runtime, repositories=self.repositories
        )

        self.assertEqual(first, second)

    def test_dirty_worktree_is_preserved(self):
        worktree = create_worktree(
            "fixture", "ACC-3", "Dirty", self.runtime, repositories=self.repositories
        )
        with open(os.path.join(worktree.path, "README.md"), "a") as readme:
            readme.write("uncommitted\n")

        self.assertFalse(remove_clean_worktree(worktree, require_pushed=False))
        self.assertTrue(os.path.isdir(worktree.path))
        self.assertFalse(inspect_worktree(worktree)["clean"])

    def test_clean_worktree_can_be_removed_after_safe_handoff(self):
        worktree = create_worktree(
            "fixture", "ACC-4", "Clean", self.runtime, repositories=self.repositories
        )

        self.assertTrue(remove_clean_worktree(worktree, require_pushed=False))
        self.assertFalse(os.path.exists(worktree.path))


if __name__ == "__main__":
    unittest.main()

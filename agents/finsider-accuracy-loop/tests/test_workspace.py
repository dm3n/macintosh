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
    verify_production_deployment,
    verify_pull_request,
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
        self.remote = os.path.join(self.root, "remote.git")
        git("init", "--bare", self.remote, cwd=self.root)
        os.makedirs(self.repo)
        git("init", "-b", "development", cwd=self.repo)
        git("config", "user.email", "daniel@nodebase.ca", cwd=self.repo)
        git("config", "user.name", "Daniel Edgar", cwd=self.repo)
        with open(os.path.join(self.repo, "README.md"), "w") as readme:
            readme.write("fixture\n")
        git("add", "README.md", cwd=self.repo)
        git("commit", "-m", "fixture", cwd=self.repo)
        git("remote", "add", "origin", self.remote, cwd=self.repo)
        git("push", "-u", "origin", "development", cwd=self.repo)
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

    def test_remote_branch_must_match_local_head_before_cleanup(self):
        worktree = create_worktree(
            "fixture", "ACC-5", "Pushed", self.runtime, repositories=self.repositories
        )
        git("push", "-u", "origin", worktree.branch, cwd=worktree.path)
        with open(os.path.join(worktree.path, "README.md"), "a") as readme:
            readme.write("second commit\n")
        git("add", "README.md", cwd=worktree.path)
        git("commit", "-m", "second", cwd=worktree.path)

        inspection = inspect_worktree(worktree)

        self.assertFalse(inspection["pushed"])
        self.assertNotEqual(inspection["remote_head"], inspection["head"])
        self.assertFalse(remove_clean_worktree(worktree, require_pushed=True))

        git("push", cwd=worktree.path)
        self.assertTrue(inspect_worktree(worktree)["pushed"])

    def test_pr_verification_requires_open_exact_head_and_cpa_label(self):
        worktree = create_worktree(
            "fixture", "ACC-6", "Delivery", self.runtime, repositories=self.repositories
        )
        head = git("rev-parse", "HEAD", cwd=worktree.path)
        git("push", "-u", "origin", worktree.branch, cwd=worktree.path)
        payload = {
            "state": "OPEN",
            "isDraft": False,
            "baseRefName": "development",
            "headRefName": worktree.branch,
            "headRefOid": head,
            "title": "NEEDS CPA REVIEW: prove cash accuracy",
            "url": "https://github.com/dm3n/fixture/pull/1",
        }

        def gh_runner(_command, **_kwargs):
            return subprocess.CompletedProcess([], 0, stdout=__import__("json").dumps(payload), stderr="")

        self.assertTrue(verify_pull_request(
            worktree, payload["url"], head, moves_customer_numbers=True, runner=gh_runner
        ))

        payload["headRefOid"] = "0" * 40
        self.assertFalse(verify_pull_request(
            worktree, payload["url"], head, moves_customer_numbers=True, runner=gh_runner
        ))

    def test_production_verification_binds_candidate_to_deployed_ref_and_workflow(self):
        git("checkout", "-b", "master", cwd=self.repo)
        git("push", "-u", "origin", "master", cwd=self.repo)
        git("checkout", "development", cwd=self.repo)
        with open(os.path.join(self.repo, "candidate.txt"), "w") as candidate_file:
            candidate_file.write("candidate\n")
        git("add", "candidate.txt", cwd=self.repo)
        git("commit", "-m", "candidate", cwd=self.repo)
        candidate_commit = git("rev-parse", "HEAD", cwd=self.repo)
        git("checkout", "master", cwd=self.repo)
        git("merge", "--ff-only", candidate_commit, cwd=self.repo)
        git("push", "origin", "master", cwd=self.repo)
        deployed_at = "2026-08-08T18:00:00Z"
        proof = {
            "candidate_commit": candidate_commit,
            "deployed_commit": candidate_commit,
            "deployed_at": deployed_at,
            "deployment_evidence_ids": [
                "github-actions:123:%s" % candidate_commit
            ],
        }

        def deployment_runner(command, **_kwargs):
            if command[:4] == ["gh", "repo", "view", "--json"]:
                payload = {"nameWithOwner": "dm3n/fixture"}
            else:
                payload = [{
                    "databaseId": 123,
                    "headSha": candidate_commit,
                    "conclusion": "success",
                    "updatedAt": deployed_at,
                    "url": "https://github.com/dm3n/fixture/actions/runs/123",
                }]
            return subprocess.CompletedProcess(
                command, 0, stdout=__import__("json").dumps(payload), stderr=""
            )

        self.assertTrue(verify_production_deployment(
            {
                "target_repo": "fixture",
                "commit": candidate_commit,
            },
            proof,
            runner=deployment_runner,
            repositories=self.repositories,
            policies={"fixture": {
                "production_branch": "master",
                "workflow": "production.yml",
            }},
        ))

        proof["deployment_evidence_ids"] = ["opaque-agent-assertion"]
        self.assertFalse(verify_production_deployment(
            {"target_repo": "fixture", "commit": candidate_commit},
            proof,
            runner=deployment_runner,
            repositories=self.repositories,
            policies={"fixture": {
                "production_branch": "master",
                "workflow": "production.yml",
            }},
        ))


if __name__ == "__main__":
    unittest.main()

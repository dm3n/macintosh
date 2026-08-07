"""Allowlisted, crash-resumable Git worktrees for Finsider fixes."""

import os
import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Repo:
    path: str
    base_branch: str


@dataclass(frozen=True)
class Worktree:
    repo_key: str
    repo_path: str
    base_branch: str
    branch: str
    path: str

    def to_dict(self):
        return {
            "repo_key": self.repo_key,
            "repo_path": self.repo_path,
            "base_branch": self.base_branch,
            "branch": self.branch,
            "path": self.path,
        }


REPOSITORIES = {
    "Mitch-be": Repo("/Users/dm3n/finsider-platform/Mitch-be", "development"),
    "Mitch-fe": Repo("/Users/dm3n/finsider-platform/Mitch-fe", "development"),
    "AI-Agents-CFO": Repo("/Users/dm3n/finsider-platform/AI-Agents-CFO", "main"),
    "finsider-excel-agent": Repo(
        "/Users/dm3n/finsider-platform/finsider-excel-agent", "main"
    ),
    "finsider-mcp": Repo("/Users/dm3n/finsider-platform/finsider-mcp", "main"),
    "finsider-agents": Repo("/Users/dm3n/finsider-platform/finsider-agents", "main"),
}


def _git(repo_path, *args, check=True):
    result = subprocess.run(
        ["git", "-C", repo_path] + list(args),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            "git %s failed in %s: %s"
            % (" ".join(args), repo_path, (result.stderr or result.stdout).strip())
        )
    return result


def _slug(value, limit=48):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "work")[:limit].rstrip("-")


def _branch_exists(repo_path, branch):
    return _git(repo_path, "show-ref", "--verify", "--quiet", "refs/heads/%s" % branch,
                check=False).returncode == 0


def _base_ref(repo):
    remote = _git(repo.path, "remote", "get-url", "origin", check=False)
    if remote.returncode == 0:
        _git(repo.path, "fetch", "--quiet", "origin", repo.base_branch)
        candidate = "origin/%s" % repo.base_branch
        if _git(repo.path, "rev-parse", "--verify", "--quiet", candidate,
                check=False).returncode == 0:
            return candidate
    if _git(repo.path, "rev-parse", "--verify", "--quiet", repo.base_branch,
            check=False).returncode != 0:
        raise RuntimeError("base branch %s does not exist in %s" % (repo.base_branch, repo.path))
    return repo.base_branch


def create_worktree(repo_key, contract_id, title, runtime_dir, repositories=None):
    repositories = repositories or REPOSITORIES
    if repo_key not in repositories:
        raise ValueError("repository is not allowlisted: %s" % repo_key)
    repo = repositories[repo_key]
    repo_path = os.path.realpath(repo.path)
    if not os.path.isdir(repo_path):
        raise ValueError("repository checkout does not exist: %s" % repo_path)

    branch = "agent/accuracy-%s-%s" % (_slug(contract_id), _slug(title))
    root = os.path.realpath(os.path.join(runtime_dir, "worktrees"))
    path = os.path.realpath(os.path.join(root, "%s-%s" % (_slug(repo_key), _slug(contract_id))))
    if os.path.commonpath((root, path)) != root:
        raise ValueError("worktree path escaped runtime directory")

    worktree = Worktree(repo_key, repo_path, repo.base_branch, branch, path)
    if os.path.exists(path):
        current = _git(path, "branch", "--show-current").stdout.strip()
        if current != branch:
            raise RuntimeError("existing worktree has unexpected branch: %s" % current)
        return worktree

    os.makedirs(root, exist_ok=True)
    if _branch_exists(repo_path, branch):
        _git(repo_path, "worktree", "add", path, branch)
    else:
        _git(repo_path, "worktree", "add", "-b", branch, path, _base_ref(repo))
    return worktree


def inspect_worktree(worktree):
    if not os.path.isdir(worktree.path):
        return {
            "exists": False,
            "clean": False,
            "branch": None,
            "head": None,
            "pushed": False,
        }
    status = _git(worktree.path, "status", "--porcelain").stdout.strip()
    branch = _git(worktree.path, "branch", "--show-current").stdout.strip()
    head = _git(worktree.path, "rev-parse", "HEAD").stdout.strip()
    remote = _git(worktree.repo_path, "remote", "get-url", "origin", check=False)
    pushed = False
    if remote.returncode == 0:
        pushed = _git(
            worktree.repo_path,
            "ls-remote",
            "--exit-code",
            "--heads",
            "origin",
            worktree.branch,
            check=False,
        ).returncode == 0
    return {
        "exists": True,
        "clean": not status,
        "branch": branch,
        "head": head,
        "pushed": pushed,
    }


def remove_clean_worktree(worktree, require_pushed=True):
    inspection = inspect_worktree(worktree)
    if not inspection["exists"]:
        return True
    if not inspection["clean"] or (require_pushed and not inspection["pushed"]):
        return False
    _git(worktree.repo_path, "worktree", "remove", worktree.path)
    return True

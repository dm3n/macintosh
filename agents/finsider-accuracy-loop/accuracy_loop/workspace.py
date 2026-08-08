"""Allowlisted, crash-resumable Git worktrees for Finsider fixes."""

import json
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

DEPLOYMENT_POLICIES = {
    "Mitch-be": {
        "production_branch": "master",
        "workflow": "master_mitch-back.yml",
    },
    "Mitch-fe": {
        "production_branch": "main",
        "environment": "Production",
    },
    "AI-Agents-CFO": {
        "production_branch": "main",
        "workflow": "deploy-production.yml",
    },
    "finsider-mcp": {
        "production_branch": "main",
        "environment": "Production",
    },
    "finsider-agents": {
        "production_branch": "main",
        "environment": "Production",
    },
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
            "remote_head": None,
            "pushed": False,
        }
    status = _git(worktree.path, "status", "--porcelain").stdout.strip()
    branch = _git(worktree.path, "branch", "--show-current").stdout.strip()
    head = _git(worktree.path, "rev-parse", "HEAD").stdout.strip()
    remote = _git(worktree.repo_path, "remote", "get-url", "origin", check=False)
    pushed = False
    remote_head = None
    if remote.returncode == 0:
        remote_ref = _git(
            worktree.repo_path,
            "ls-remote",
            "--heads",
            "origin",
            worktree.branch,
            check=False,
        )
        if remote_ref.returncode == 0 and remote_ref.stdout.strip():
            remote_head = remote_ref.stdout.split()[0]
            pushed = remote_head == head
    return {
        "exists": True,
        "clean": not status,
        "branch": branch,
        "head": head,
        "remote_head": remote_head,
        "pushed": pushed,
    }


def verify_pull_request(
    worktree, pr_url, expected_commit, moves_customer_numbers, runner=subprocess.run
):
    inspection = inspect_worktree(worktree)
    if not inspection["exists"] or not inspection["clean"] or not inspection["pushed"]:
        return False
    if inspection["branch"] != worktree.branch or inspection["head"] != expected_commit:
        return False
    result = runner(
        [
            "gh", "pr", "view", pr_url, "--json",
            "state,isDraft,baseRefName,headRefName,headRefOid,title,url",
        ],
        cwd=worktree.path,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("unable to inspect PR handoff: %s" % result.stderr.strip())
    try:
        payload = json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError("gh returned malformed PR metadata") from error
    expected = (
        payload.get("state") == "OPEN"
        and payload.get("isDraft") is False
        and payload.get("baseRefName") == worktree.base_branch
        and payload.get("headRefName") == worktree.branch
        and payload.get("headRefOid") == expected_commit
        and payload.get("url") == pr_url
    )
    if not expected:
        return False
    if moves_customer_numbers and "NEEDS CPA REVIEW" not in payload.get("title", ""):
        return False
    return True


def _github_repository(repo_path, runner):
    result = runner(
        ["gh", "repo", "view", "--json", "nameWithOwner"],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("unable to identify GitHub repository")
    try:
        return json.loads(result.stdout)["nameWithOwner"]
    except (KeyError, ValueError) as error:
        raise RuntimeError("gh returned malformed repository metadata") from error


def _workflow_deployment_record(
    repo_path, repository, workflow, candidate_commit, deployed_commit, runner
):
    result = runner(
        [
            "gh", "run", "list", "--repo", repository, "--workflow", workflow,
            "--commit", deployed_commit, "--status", "success", "--limit", "20",
            "--json", "databaseId,headSha,conclusion,updatedAt,url",
        ],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("unable to inspect production deployment workflow")
    try:
        runs = json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError("gh returned malformed deployment workflow metadata") from error
    for run in runs:
        evidence_id = "github-actions:%s:%s" % (
            run.get("databaseId"), run.get("headSha")
        )
        if (
            run.get("conclusion") == "success"
            and run.get("headSha") == deployed_commit
            and isinstance(run.get("updatedAt"), str)
        ):
            return {
                "verified": True,
                "candidate_commit": candidate_commit,
                "deployed_commit": deployed_commit,
                "deployed_at": run["updatedAt"],
                "deployment_evidence_id": evidence_id,
                "deployment_url": run.get("url"),
            }
    return None


def _environment_deployment_record(
    repo_path, repository, environment, candidate_commit, deployed_commit, runner
):
    deployments_result = runner(
        [
            "gh", "api",
            "repos/%s/deployments?sha=%s&environment=%s&per_page=20"
            % (repository, deployed_commit, environment),
        ],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    if deployments_result.returncode != 0:
        raise RuntimeError("unable to inspect production deployment records")
    try:
        deployments = json.loads(deployments_result.stdout)
    except ValueError as error:
        raise RuntimeError("gh returned malformed deployment records") from error
    for deployment in deployments:
        deployment_id = deployment.get("id")
        if deployment.get("sha") != deployed_commit or not deployment_id:
            continue
        statuses_result = runner(
            [
                "gh", "api",
                "repos/%s/deployments/%s/statuses?per_page=20"
                % (repository, deployment_id),
            ],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        if statuses_result.returncode != 0:
            raise RuntimeError("unable to inspect production deployment status")
        try:
            statuses = json.loads(statuses_result.stdout)
        except ValueError as error:
            raise RuntimeError("gh returned malformed deployment status") from error
        evidence_id = "github-deployment:%s:%s:%s" % (
            deployment_id, deployed_commit, environment
        )
        for status in statuses:
            if status.get("state") == "success" and isinstance(
                status.get("created_at"), str
            ):
                return {
                    "verified": True,
                    "candidate_commit": candidate_commit,
                    "deployed_commit": deployed_commit,
                    "deployed_at": status["created_at"],
                    "deployment_evidence_id": evidence_id,
                    "deployment_url": status.get("target_url") or status.get(
                        "environment_url"
                    ),
                }
    return None


def production_deployment_record(
    candidate, runner=subprocess.run, repositories=None, policies=None
):
    """Return trusted current-production evidence only when it contains the candidate."""
    repositories = repositories or REPOSITORIES
    policies = policies or DEPLOYMENT_POLICIES
    repo_key = candidate.get("target_repo")
    repo = repositories.get(repo_key)
    policy = policies.get(repo_key)
    if repo is None or policy is None or not os.path.isdir(repo.path):
        return None
    candidate_commit = candidate.get("commit")
    if not isinstance(candidate_commit, str) or not candidate_commit:
        return None
    production_branch = policy.get("production_branch")
    if not production_branch:
        return None
    _git(repo.path, "fetch", "--quiet", "origin", production_branch)
    production_ref = "origin/%s" % production_branch
    deployed = _git(repo.path, "rev-parse", production_ref, check=False)
    if deployed.returncode != 0:
        return None
    deployed_commit = deployed.stdout.strip()
    if _git(
        repo.path, "merge-base", "--is-ancestor", candidate_commit, deployed_commit,
        check=False,
    ).returncode != 0:
        return None
    repository = _github_repository(repo.path, runner)
    if policy.get("workflow"):
        return _workflow_deployment_record(
            repo.path, repository, policy["workflow"], candidate_commit,
            deployed_commit, runner
        )
    if policy.get("environment"):
        return _environment_deployment_record(
            repo.path, repository, policy["environment"], candidate_commit,
            deployed_commit, runner
        )
    return None


def verify_production_deployment(
    candidate, proof, runner=subprocess.run, repositories=None, policies=None
):
    """Bind an agent proof to independently discovered production evidence."""
    record = production_deployment_record(
        candidate, runner=runner, repositories=repositories, policies=policies
    )
    if record is None:
        return False
    return (
        proof.get("candidate_commit") == record["candidate_commit"]
        and proof.get("deployed_commit") == record["deployed_commit"]
        and proof.get("deployed_at") == record["deployed_at"]
        and record["deployment_evidence_id"] in proof.get(
            "deployment_evidence_ids", []
        )
    )


def remove_clean_worktree(worktree, require_pushed=True):
    inspection = inspect_worktree(worktree)
    if not inspection["exists"]:
        return True
    if not inspection["clean"] or (require_pushed and not inspection["pushed"]):
        return False
    _git(worktree.repo_path, "worktree", "remove", worktree.path)
    return True

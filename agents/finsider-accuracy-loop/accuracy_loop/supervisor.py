"""Crash-resumable spec -> build -> judge accuracy supervisor."""

import copy
import fcntl
import json
import os
import shutil
import signal
import time
from datetime import datetime, timedelta, timezone
from threading import Event

from .claude import AgentFailure, ClaudeRunner
from .model import (
    REQUIRED_DOMAINS,
    advance_phase,
    load_state,
    new_state,
    record_accepted_sweep,
    save_state,
    utc_now,
)
from .workspace import REPOSITORIES, Worktree, create_worktree, remove_clean_worktree


SPEC_SCHEMA = {
    "type": "object",
    "required": ["decision", "summary", "contract", "blockers", "coverage_observations"],
    "properties": {
        "decision": {"enum": ["code", "operations", "proof"]},
        "summary": {"type": "string"},
        "contract": {
            "type": "object",
            "required": [
                "id", "title", "action", "target_repo", "domain", "workspace_names",
                "root_cause_hypothesis", "acceptance_assertions", "verification_plan",
                "moves_customer_numbers", "idempotency_key",
            ],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "action": {"enum": ["code", "operations", "proof"]},
                "target_repo": {"type": ["string", "null"]},
                "domain": {"enum": list(REQUIRED_DOMAINS)},
                "workspace_names": {"type": "array", "items": {"type": "string"}},
                "root_cause_hypothesis": {"type": "string"},
                "acceptance_assertions": {"type": "array", "items": {"type": "string"}},
                "verification_plan": {"type": "array", "items": {"type": "string"}},
                "moves_customer_numbers": {"type": "boolean"},
                "idempotency_key": {"type": "string"},
            },
        },
        "blockers": {"type": "array", "items": {"type": "object"}},
        "coverage_observations": {"type": "object"},
    },
}

BUILD_SCHEMA = {
    "type": "object",
    "required": [
        "outcome", "summary", "branch", "commit", "pr_url", "ticket_urls", "tests",
        "evidence", "moves_customer_numbers", "wait_seconds",
    ],
    "properties": {
        "outcome": {"enum": ["ready_for_judge", "blocked", "failed"]},
        "summary": {"type": "string"},
        "branch": {"type": ["string", "null"]},
        "commit": {"type": ["string", "null"]},
        "pr_url": {"type": ["string", "null"]},
        "ticket_urls": {"type": "array", "items": {"type": "string"}},
        "tests": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "moves_customer_numbers": {"type": "boolean"},
        "wait_seconds": {"type": "integer", "minimum": 0, "maximum": 300},
        "full_sweep": {"type": "object"},
    },
}

JUDGE_SCHEMA = {
    "type": "object",
    "required": [
        "verdict", "score", "summary", "hard_gates", "findings", "rework_instructions",
        "verified_evidence", "coverage_updates", "blockers", "wait_seconds",
    ],
    "properties": {
        "verdict": {"enum": ["ACCEPT", "REJECT", "BLOCKED"]},
        "score": {"type": "number", "minimum": 0, "maximum": 1},
        "summary": {"type": "string"},
        "hard_gates": {
            "type": "object",
            "required": [
                "contract_met", "regression_evidence", "source_reconciled", "freshness", "safety"
            ],
            "properties": {
                "contract_met": {"type": "boolean"},
                "regression_evidence": {"type": "boolean"},
                "source_reconciled": {"type": "boolean"},
                "freshness": {"type": "boolean"},
                "safety": {"type": "boolean"},
            },
        },
        "findings": {"type": "array", "items": {"type": "string"}},
        "rework_instructions": {"type": "array", "items": {"type": "string"}},
        "verified_evidence": {"type": "array", "items": {"type": "string"}},
        "coverage_updates": {"type": "object"},
        "blockers": {"type": "array", "items": {"type": "object"}},
        "wait_seconds": {"type": "integer", "minimum": 0, "maximum": 300},
        "full_sweep": {"type": "object"},
    },
}


def _retry_timestamp(attempts):
    delay = min(300, 30 * (2 ** min(attempts - 1, 4)))
    return (
        datetime.now(timezone.utc) + timedelta(seconds=delay)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bounded_wait(value):
    if not isinstance(value, int):
        return 0
    return max(0, min(300, value))


class Supervisor:
    def __init__(
        self,
        runtime_dir,
        source_dir,
        finsider_dir="/Users/dm3n/finsider-platform",
        runner=None,
        create_worktree_fn=create_worktree,
        remove_worktree_fn=remove_clean_worktree,
        sleep_fn=time.sleep,
    ):
        self.runtime_dir = os.path.abspath(runtime_dir)
        self.source_dir = os.path.abspath(source_dir)
        self.finsider_dir = os.path.abspath(finsider_dir)
        self.state_path = os.path.join(self.runtime_dir, "STATE.json")
        self.contract_path = os.path.join(self.runtime_dir, "CONTRACT.md")
        self.ledger_path = os.path.join(self.runtime_dir, "LEDGER.md")
        self.trace_dir = os.path.join(self.runtime_dir, "traces")
        self.runner = runner or ClaudeRunner(trace_dir=self.trace_dir)
        self.create_worktree_fn = create_worktree_fn
        self.remove_worktree_fn = remove_worktree_fn
        self.sleep_fn = sleep_fn
        self.stop_event = Event()
        self._lock_file = None

    def ensure_runtime(self):
        os.makedirs(self.runtime_dir, exist_ok=True)
        os.makedirs(self.trace_dir, exist_ok=True)
        os.makedirs(os.path.join(self.runtime_dir, "worktrees"), exist_ok=True)
        if not os.path.exists(self.contract_path):
            shutil.copyfile(os.path.join(self.source_dir, "contract.md"), self.contract_path)
        if not os.path.exists(self.state_path):
            save_state(self.state_path, new_state())
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, "w") as ledger:
                ledger.write("# Finsider Continuous Accuracy Loop Ledger\n\n")

    def _append_ledger(self, phase, outcome, summary):
        safe_summary = " ".join(str(summary).splitlines()).strip()
        with open(self.ledger_path, "a") as ledger:
            ledger.write("- %s | %s | %s | %s\n" % (utc_now(), phase, outcome, safe_summary))

    def _read_prompt(self, phase):
        filename = "build.md" if phase == "rework" else phase + ".md"
        with open(os.path.join(self.source_dir, "prompts", filename)) as prompt_file:
            return prompt_file.read()

    def _render_prompt(self, phase, state):
        with open(self.contract_path) as contract_file:
            global_contract = contract_file.read()
        context = {
            "cycle": state.get("cycle"),
            "phase": phase,
            "coverage": state.get("coverage"),
            "blockers": state.get("blockers"),
            "active_contract": state.get("active_contract"),
            "spec_result": state.get("spec_result"),
            "build_result": state.get("build_result"),
            "judge_result": state.get("judge_result"),
            "rework_count": state.get("rework_count"),
            "legacy_measurement_ledger": "/Users/dm3n/.claude/scripts/tieout-loop/LEDGER.md",
            "legacy_fix_ledger": "/Users/dm3n/finsider-platform/.accuracy-fix-loop/LEDGER.md",
        }
        return "%s\n\n## GLOBAL_CONTRACT\n%s\n\n## SUPERVISOR_CONTEXT\n%s\n" % (
            self._read_prompt(phase),
            global_contract,
            json.dumps(context, indent=2, sort_keys=True),
        )

    def _worktree_from_state(self, state):
        data = state.get("worktree")
        return Worktree(**data) if data else None

    def _phase_cwd(self, state):
        worktree = self._worktree_from_state(state)
        return worktree.path if worktree else self.finsider_dir

    def _prepare_code_worktree(self, state):
        existing = self._worktree_from_state(state)
        if existing:
            return existing
        work_unit = state["active_contract"]
        worktree = self.create_worktree_fn(
            work_unit["target_repo"],
            work_unit["id"],
            work_unit["title"],
            self.runtime_dir,
        )
        state["worktree"] = worktree.to_dict()
        save_state(self.state_path, state)
        return worktree

    def _apply_coverage(self, state, updates):
        if not isinstance(updates, dict):
            return
        for domain, proof in updates.items():
            if domain not in REQUIRED_DOMAINS or not isinstance(proof, dict):
                continue
            if proof.get("status") not in ("unknown", "partial", "proved"):
                continue
            evidence = proof.get("evidence", [])
            if not isinstance(evidence, list):
                continue
            state["coverage"][domain] = {
                "status": proof["status"],
                "evidence": evidence,
                "updated_at": utc_now(),
            }

    def _validate_contract(self, result):
        work_unit = result.get("contract", {})
        action = work_unit.get("action")
        if result.get("decision") != action:
            raise AgentFailure("spec decision and contract action disagree")
        if work_unit.get("domain") not in REQUIRED_DOMAINS:
            raise AgentFailure("spec selected an unknown accuracy domain")
        if not work_unit.get("id") or not work_unit.get("title"):
            raise AgentFailure("spec contract is missing its identity")
        if not work_unit.get("idempotency_key"):
            raise AgentFailure("spec contract is missing its idempotency key")
        if not work_unit.get("acceptance_assertions") or not work_unit.get("verification_plan"):
            raise AgentFailure("spec contract has no testable assertions")
        target_repo = work_unit.get("target_repo")
        if action == "code" and target_repo not in REPOSITORIES:
            raise AgentFailure("code contract target repository is not allowlisted")
        if action in ("operations", "proof") and target_repo is not None:
            raise AgentFailure("non-code contract cannot target a repository")

    def _judge_accepts(self, state, result):
        gates = result.get("hard_gates", {})
        required_gates = (
            "contract_met", "regression_evidence", "source_reconciled", "freshness", "safety"
        )
        accepted = (
            result.get("verdict") == "ACCEPT"
            and result.get("score", 0) >= 0.90
            and all(gates.get(gate) is True for gate in required_gates)
        )
        if not accepted:
            return False
        work_unit = state.get("active_contract") or {}
        build = state.get("build_result") or {}
        if build.get("outcome") != "ready_for_judge" or not build.get("evidence"):
            return False
        if work_unit.get("action") == "code":
            delivery_fields = (build.get("branch"), build.get("commit"), build.get("pr_url"))
            if not all(isinstance(value, str) and value for value in delivery_fields):
                return False
            if not build.get("tests"):
                return False
            if work_unit.get("moves_customer_numbers") is True and build.get(
                "moves_customer_numbers"
            ) is not True:
                return False
        return True

    def _reset_cycle(self, state, wait_seconds=0):
        state["phase"] = "spec"
        state["phase_attempts"] = 0
        state["active_contract"] = None
        state["spec_result"] = None
        state["build_result"] = None
        state["judge_result"] = None
        state["worktree"] = None
        state["rework_count"] = 0
        state["last_error"] = None
        wait_seconds = _bounded_wait(wait_seconds)
        if wait_seconds:
            state["retry_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=wait_seconds)
            ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        else:
            state["retry_at"] = None

    def _record_blocker(self, state, result):
        work_unit = state.get("active_contract") or {}
        state["blockers"].append({
            "contract_id": work_unit.get("id"),
            "title": work_unit.get("title"),
            "summary": result.get("summary"),
            "findings": result.get("findings", []),
            "external_blockers": result.get("blockers", []),
            "worktree": state.get("worktree"),
            "recorded_at": utc_now(),
        })

    def _cleanup_delivered_worktree(self, state):
        worktree = self._worktree_from_state(state)
        build = state.get("build_result") or {}
        if worktree and build.get("pr_url"):
            self.remove_worktree_fn(worktree, require_pushed=True)

    def _run_spec(self, state):
        result = self.runner.run(
            "spec", self._render_prompt("spec", state), SPEC_SCHEMA, self.finsider_dir
        )
        self._validate_contract(result)
        state["cycle"] += 1
        state["spec_result"] = result
        state["active_contract"] = result["contract"]
        state["blockers"].extend(result.get("blockers", []))
        state = advance_phase(state, "build")
        save_state(self.state_path, state)
        self._append_ledger("spec", "contracted", result["summary"])
        return "build"

    def _run_build(self, state, rework=False):
        if state["active_contract"]["action"] == "code":
            self._prepare_code_worktree(state)
        phase = "rework" if rework else "build"
        result = self.runner.run(
            phase, self._render_prompt(phase, state), BUILD_SCHEMA, self._phase_cwd(state)
        )
        state["build_result"] = result
        state = advance_phase(state, "judge")
        save_state(self.state_path, state)
        self._append_ledger(phase, result["outcome"], result["summary"])
        return "judge"

    def _run_judge(self, state):
        result = self.runner.run(
            "judge", self._render_prompt("judge", state), JUDGE_SCHEMA, self._phase_cwd(state)
        )
        state["judge_result"] = result
        accepted = self._judge_accepts(state, result)
        work_unit = state["active_contract"]
        if accepted:
            self._apply_coverage(state, result.get("coverage_updates"))
            full_sweep = result.get("full_sweep")
            completed = False
            if isinstance(full_sweep, dict):
                audited_sweep = copy.deepcopy(full_sweep)
                audited_sweep["judge_verdict"] = "ACCEPT"
                completed = record_accepted_sweep(state, audited_sweep)
            self._cleanup_delivered_worktree(state)
            self._append_ledger("judge", "ACCEPT", result["summary"])
            if completed:
                state["phase"] = "judge"
                save_state(self.state_path, state)
                self._append_ledger("supervisor", "PROOF-COMPLETE", "Two clean sweeps accepted")
                return "complete"
            self._reset_cycle(state)
            save_state(self.state_path, state)
            return "spec"

        if (
            result.get("verdict") != "BLOCKED"
            and work_unit["action"] == "code"
            and state.get("rework_count", 0) == 0
        ):
            state["rework_count"] = 1
            state = advance_phase(state, "rework")
            state["judge_result"] = result
            save_state(self.state_path, state)
            self._append_ledger("judge", "REJECT-REWORK", result["summary"])
            return "rework"

        self._record_blocker(state, result)
        self._append_ledger("judge", result.get("verdict", "REJECT"), result["summary"])
        self._reset_cycle(state, result.get("wait_seconds", 0))
        save_state(self.state_path, state)
        return "spec"

    def step(self):
        self.ensure_runtime()
        state = load_state(self.state_path)
        if state.get("status") == "complete":
            return "complete"
        phase = state["phase"]
        try:
            if phase == "spec":
                return self._run_spec(state)
            if phase == "build":
                return self._run_build(state)
            if phase == "rework":
                return self._run_build(state, rework=True)
            if phase == "judge":
                return self._run_judge(state)
            raise RuntimeError("unknown persisted phase: %s" % phase)
        except AgentFailure as error:
            state = load_state(self.state_path)
            state["phase_attempts"] = state.get("phase_attempts", 0) + 1
            state["last_error"] = str(error)
            state["retry_at"] = _retry_timestamp(state["phase_attempts"])
            save_state(self.state_path, state)
            self._append_ledger(phase, "RETRY", str(error))
            return "retry"

    def request_stop(self, *_args):
        self.stop_event.set()
        self.runner.terminate()

    def _seconds_until_retry(self, state):
        retry_at = state.get("retry_at")
        if not retry_at:
            return 0
        target = datetime.fromisoformat(retry_at.replace("Z", "+00:00"))
        return max(0, int((target - datetime.now(timezone.utc)).total_seconds()))

    def _acquire_lock(self):
        lock_path = os.path.join(self.trace_dir, ".supervisor.lock")
        self._lock_file = open(lock_path, "w")
        try:
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("another accuracy supervisor is already running") from error
        self._lock_file.write(str(os.getpid()))
        self._lock_file.flush()

    def run_forever(self):
        self.ensure_runtime()
        self._acquire_lock()
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)
        self._append_ledger("supervisor", "START", "Persistent loop started")
        while not self.stop_event.is_set():
            state = load_state(self.state_path)
            if state.get("status") == "complete":
                return 0
            remaining = self._seconds_until_retry(state)
            if remaining:
                self.sleep_fn(min(5, remaining))
                continue
            outcome = self.step()
            if outcome == "complete":
                return 0
        self._append_ledger("supervisor", "STOP", "Signal received; resumable state saved")
        return 0

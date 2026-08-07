"""Crash-resumable spec -> build -> judge accuracy supervisor."""

import copy
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta, timezone
from threading import Event

from .claude import AgentFailure, ClaudeRunner
from .model import (
    LIFECYCLE_STATES,
    REQUIRED_DIMENSIONS,
    REQUIRED_DOMAINS,
    REQUIRED_LAYERS,
    REQUIRED_SURFACES,
    advance_phase,
    load_state,
    new_state,
    record_accepted_sweep,
    save_state,
    utc_now,
)
from .workspace import (
    REPOSITORIES,
    Worktree,
    create_worktree,
    remove_clean_worktree,
    verify_pull_request,
)


STRUCTURED_EVIDENCE_SCHEMA = {
    "type": "object",
    "required": [
        "kind", "id", "source", "observed_at", "workspace_ids", "periods",
        "layers", "dimensions", "surfaces",
    ],
    "properties": {
        "kind": {"type": "string"},
        "id": {"type": "string"},
        "source": {"type": "string"},
        "observed_at": {"type": "string"},
        "workspace_ids": {"type": "array", "items": {"type": "string"}},
        "periods": {"type": "array", "items": {"type": "string"}},
        "layers": {"type": "array", "items": {"type": "string"}},
        "dimensions": {"type": "array", "items": {"type": "string"}},
        "surfaces": {"type": "array", "items": {"type": "string"}},
    },
}

PROOF_SCHEMA = {
    "type": "object",
    "required": ["status", "evidence"],
    "properties": {
        "status": {"enum": ["unknown", "partial", "proved"]},
        "evidence": {"type": "array", "items": STRUCTURED_EVIDENCE_SCHEMA},
    },
}

FULL_SWEEP_SCHEMA = {
    "type": "object",
    "required": [
        "sweep_id", "observed_at", "data_watermark", "latest_sync_watermark",
        "latest_deploy_watermark", "active_workspaces", "verified_workspaces",
        "mismatches", "errors", "unknowns", "stale", "unresolved_surfaces",
        "onboarding_gate_verified", "authoritative_roster", "workspace_roster", "domains",
        "scope",
    ],
    "properties": {
        "sweep_id": {"type": "string"},
        "observed_at": {"type": "string"},
        "data_watermark": {"type": "string"},
        "latest_sync_watermark": {"type": "string"},
        "latest_deploy_watermark": {"type": "string"},
        "active_workspaces": {"type": "integer"},
        "verified_workspaces": {"type": "integer"},
        "mismatches": {"type": "integer"},
        "errors": {"type": "integer"},
        "unknowns": {"type": "integer"},
        "stale": {"type": "integer"},
        "unresolved_surfaces": {"type": "integer"},
        "onboarding_gate_verified": {"type": "boolean"},
        "authoritative_roster": {
            "type": "object",
            "required": [
                "kind", "id", "source", "observed_at", "workspace_ids", "checksum",
            ],
            "properties": {
                "kind": {"enum": ["authoritative_workspace_roster"]},
                "id": {"type": "string"},
                "source": {"enum": ["finsider-verification:list_workspaces"]},
                "observed_at": {"type": "string"},
                "workspace_ids": {"type": "array", "items": {"type": "string"}},
                "checksum": {"type": "string"},
            },
        },
        "workspace_roster": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["workspace_id", "name", "lifecycle", "included"],
                "properties": {
                    "workspace_id": {"type": "string"},
                    "name": {"type": "string"},
                    "lifecycle": {"enum": list(LIFECYCLE_STATES)},
                    "included": {"type": "boolean"},
                    "latest_sync_at": {"type": "string"},
                    "verification_id": {"type": "string"},
                    "verified_at": {"type": "string"},
                    "exclusion_reason": {"type": "string"},
                },
            },
        },
        "domains": {
            "type": "object",
            "required": list(REQUIRED_DOMAINS),
            "properties": {domain: PROOF_SCHEMA for domain in REQUIRED_DOMAINS},
        },
        "scope": {
            "type": "object",
            "required": ["periods", "layers", "dimensions", "surfaces"],
            "properties": {
                "periods": {
                    "type": "object",
                    "required": ["coverage", "evidence"],
                    "properties": {
                        "coverage": {"enum": ["all_supported_history"]},
                        "evidence": {"type": "array", "items": STRUCTURED_EVIDENCE_SCHEMA},
                    },
                },
                "layers": {
                    "type": "object",
                    "required": ["required", "covered", "evidence"],
                    "properties": {
                        "required": {"type": "array", "items": {"enum": list(REQUIRED_LAYERS)}},
                        "covered": {"type": "array", "items": {"enum": list(REQUIRED_LAYERS)}},
                        "evidence": {"type": "array", "items": STRUCTURED_EVIDENCE_SCHEMA},
                    },
                },
                "dimensions": {
                    "type": "object",
                    "required": ["required", "covered", "evidence"],
                    "properties": {
                        "required": {"type": "array", "items": {"enum": list(REQUIRED_DIMENSIONS)}},
                        "covered": {"type": "array", "items": {"enum": list(REQUIRED_DIMENSIONS)}},
                        "evidence": {"type": "array", "items": STRUCTURED_EVIDENCE_SCHEMA},
                    },
                },
                "surfaces": {
                    "type": "object",
                    "required": list(REQUIRED_SURFACES),
                    "properties": {surface: PROOF_SCHEMA for surface in REQUIRED_SURFACES},
                },
            },
        },
    },
}

BLOCKER_SCHEMA = {
    "type": "object",
    "required": ["id", "summary", "owner", "evidence_needed"],
    "properties": {
        "id": {"type": "string"},
        "summary": {"type": "string"},
        "owner": {"type": "string"},
        "evidence_needed": {"type": "array", "items": {"type": "string"}},
    },
}

RECEIPT_SCHEMA = {
    "type": "object",
    "required": ["kind", "id", "url", "status"],
    "properties": {
        "kind": {"enum": [
            "verification_run", "roster_snapshot", "source_snapshot", "ui_probe",
            "export_artifact", "test_run", "pull_request", "jira", "other",
        ]},
        "id": {"type": "string"},
        "url": {"type": ["string", "null"]},
        "status": {"type": "string"},
    },
}


SPEC_SCHEMA = {
    "type": "object",
    "required": [
        "decision", "summary", "contract", "blockers", "resolved_blocker_ids",
        "coverage_observations",
    ],
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
        "blockers": {"type": "array", "items": BLOCKER_SCHEMA},
        "resolved_blocker_ids": {"type": "array", "items": {"type": "string"}},
        "coverage_observations": {"type": "object"},
    },
}

BUILD_SCHEMA = {
    "type": "object",
    "required": [
        "outcome", "summary", "branch", "commit", "pr_url", "ticket_urls", "tests",
        "evidence", "receipts", "moves_customer_numbers", "wait_seconds",
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
        "receipts": {"type": "array", "items": RECEIPT_SCHEMA},
        "moves_customer_numbers": {"type": "boolean"},
        "wait_seconds": {"type": "integer", "minimum": 0, "maximum": 300},
        "full_sweep": FULL_SWEEP_SCHEMA,
    },
}

JUDGE_SCHEMA = {
    "type": "object",
    "required": [
        "verdict", "score", "summary", "hard_gates", "findings", "rework_instructions",
        "verified_evidence", "coverage_updates", "blockers", "resolved_blocker_ids",
        "wait_seconds",
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
        "blockers": {"type": "array", "items": BLOCKER_SCHEMA},
        "resolved_blocker_ids": {"type": "array", "items": {"type": "string"}},
        "wait_seconds": {"type": "integer", "minimum": 0, "maximum": 300},
        "full_sweep": FULL_SWEEP_SCHEMA,
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
        verify_delivery_fn=verify_pull_request,
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
        self.verify_delivery_fn = verify_delivery_fn
        self.sleep_fn = sleep_fn
        self.stop_event = Event()
        self._lock_file = None

    def ensure_runtime(self):
        os.makedirs(self.runtime_dir, exist_ok=True)
        os.makedirs(self.trace_dir, exist_ok=True)
        os.makedirs(os.path.join(self.runtime_dir, "worktrees"), exist_ok=True)
        source_contract_path = os.path.join(self.source_dir, "contract.md")
        with open(source_contract_path, "rb") as contract_file:
            contract_content = contract_file.read()
        contract_hash = hashlib.sha256(contract_content).hexdigest()
        current_contract = None
        if os.path.exists(self.contract_path):
            with open(self.contract_path, "rb") as contract_file:
                current_contract = contract_file.read()
        if current_contract != contract_content:
            temporary_contract = self.contract_path + ".tmp"
            with open(temporary_contract, "wb") as contract_file:
                contract_file.write(contract_content)
                contract_file.flush()
                os.fsync(contract_file.fileno())
            os.replace(temporary_contract, self.contract_path)
        if not os.path.exists(self.state_path):
            state = new_state()
            state["contract_sha256"] = contract_hash
            save_state(self.state_path, state)
        else:
            state = load_state(self.state_path)
            if state.get("contract_sha256") != contract_hash:
                state["contract_sha256"] = contract_hash
                state["clean_sweeps"] = []
                state["status"] = "running"
                state["last_sweep_errors"] = [
                    "accuracy contract changed; proof sequence restarted"
                ]
                save_state(self.state_path, state)
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
            "action_intent": state.get("action_intent"),
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
        if not work_unit.get("acceptance_assertions") or not work_unit.get("verification_plan"):
            raise AgentFailure("spec contract has no testable assertions")
        target_repo = work_unit.get("target_repo")
        if action == "code" and target_repo not in REPOSITORIES:
            raise AgentFailure("code contract target repository is not allowlisted")
        if action in ("operations", "proof") and target_repo is not None:
            raise AgentFailure("non-code contract cannot target a repository")

    def _derive_idempotency_key(self, work_unit):
        identity = {
            key: work_unit.get(key)
            for key in (
                "id", "title", "action", "target_repo", "domain", "workspace_names",
                "acceptance_assertions", "verification_plan", "moves_customer_numbers",
            )
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:20]
        return "finsider-accuracy:%s:%s" % (work_unit["id"], digest)

    def _reconcile_blockers(self, state, result):
        resolved = set(result.get("resolved_blocker_ids", []))
        by_id = {
            blocker.get("id"): blocker
            for blocker in state.get("blockers", [])
            if isinstance(blocker, dict) and blocker.get("id") not in resolved
        }
        for blocker in result.get("blockers", []):
            if blocker.get("id"):
                by_id[blocker["id"]] = copy.deepcopy(blocker)
        state["blockers"] = list(by_id.values())

    def _resolve_accepted_blockers(self, state, result):
        resolved = set(result.get("resolved_blocker_ids", []))
        state["blockers"] = [
            blocker for blocker in state.get("blockers", [])
            if blocker.get("id") not in resolved
        ]

    def _full_sweep_is_corroborated(self, state, judge_sweep, result):
        build = state.get("build_result") or {}
        build_sweep = build.get("full_sweep")
        if not isinstance(build_sweep, dict) or build_sweep != judge_sweep:
            return False
        required_ids = {judge_sweep["authoritative_roster"]["id"]}
        required_ids.update(
            workspace["verification_id"]
            for workspace in judge_sweep["workspace_roster"]
            if workspace.get("lifecycle") == "active"
        )
        evidence_lists = []
        for proof in judge_sweep["domains"].values():
            evidence_lists.append(proof["evidence"])
        scope = judge_sweep["scope"]
        for key in ("periods", "layers", "dimensions"):
            evidence_lists.append(scope[key]["evidence"])
        for proof in scope["surfaces"].values():
            evidence_lists.append(proof["evidence"])
        for evidence in evidence_lists:
            required_ids.update(item["id"] for item in evidence)
        receipt_ids = {
            receipt.get("id")
            for receipt in build.get("receipts", [])
            if receipt.get("status") == "complete"
        }
        judge_ids = set(result.get("verified_evidence", []))
        return required_ids.issubset(receipt_ids) and required_ids.issubset(judge_ids)

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
        if (
            build.get("outcome") != "ready_for_judge"
            or not build.get("evidence")
            or not build.get("receipts")
        ):
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
            worktree = self._worktree_from_state(state)
            if worktree is None or not self.verify_delivery_fn(
                worktree,
                build["pr_url"],
                build["commit"],
                work_unit.get("moves_customer_numbers") is True,
            ):
                return False
        return True

    def _reset_cycle(self, state, wait_seconds=0):
        state["phase"] = "spec"
        state["phase_attempts"] = 0
        state["active_contract"] = None
        state["spec_result"] = None
        state["build_result"] = None
        state["judge_result"] = None
        state["action_intent"] = None
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
        external = result.get("blockers", [])
        first = external[0] if external and isinstance(external[0], dict) else {}
        blocker = {
            "id": first.get("id") or work_unit.get("id"),
            "summary": result.get("summary"),
            "owner": first.get("owner") or "Finsider accuracy loop",
            "evidence_needed": first.get("evidence_needed") or result.get(
                "rework_instructions", []
            ) or result.get("findings", []),
            "contract_id": work_unit.get("id"),
            "title": work_unit.get("title"),
            "worktree": state.get("worktree"),
            "recorded_at": utc_now(),
        }
        state["blockers"] = [
            existing for existing in state.get("blockers", [])
            if existing.get("id") != blocker["id"]
        ] + [blocker]

    def _cleanup_delivered_worktree(self, worktree, build):
        if worktree and build.get("pr_url"):
            self.remove_worktree_fn(worktree, require_pushed=True)

    def _run_spec(self, state):
        result = self.runner.run(
            "spec", self._render_prompt("spec", state), SPEC_SCHEMA, self.finsider_dir
        )
        self._validate_contract(result)
        result["contract"]["idempotency_key"] = self._derive_idempotency_key(
            result["contract"]
        )
        state["cycle"] += 1
        state["spec_result"] = result
        state["active_contract"] = result["contract"]
        self._reconcile_blockers(state, result)
        state = advance_phase(state, "build")
        save_state(self.state_path, state)
        self._append_ledger("spec", "contracted", result["summary"])
        return "build"

    def _run_build(self, state, rework=False):
        if state["active_contract"]["action"] == "code":
            self._prepare_code_worktree(state)
        phase = "rework" if rework else "build"
        if state.get("action_intent") is None:
            state["action_intent"] = {
                "idempotency_key": state["active_contract"]["idempotency_key"],
                "started_at": utc_now(),
                "receipts": [],
            }
            save_state(self.state_path, state)
        result = self.runner.run(
            phase,
            self._render_prompt(phase, state),
            BUILD_SCHEMA,
            self._phase_cwd(state),
            capability_phase=("rework" if rework else state["active_contract"]["action"]),
        )
        state["build_result"] = result
        state["action_intent"]["receipts"] = copy.deepcopy(result.get("receipts", []))
        wait_seconds = _bounded_wait(result.get("wait_seconds", 0))
        if result.get("outcome") == "blocked" and wait_seconds:
            state["retry_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=wait_seconds)
            ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            save_state(self.state_path, state)
            self._append_ledger(phase, "WAIT", result["summary"])
            return "retry"
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
            delivered_worktree = self._worktree_from_state(state)
            delivered_build = state.get("build_result") or {}
            self._resolve_accepted_blockers(state, result)
            self._apply_coverage(state, result.get("coverage_updates"))
            full_sweep = result.get("full_sweep")
            completed = False
            if isinstance(full_sweep, dict) and self._full_sweep_is_corroborated(
                state, full_sweep, result
            ):
                audited_sweep = copy.deepcopy(full_sweep)
                audited_sweep["judge_verdict"] = "ACCEPT"
                completed = record_accepted_sweep(state, audited_sweep)
            elif isinstance(full_sweep, dict):
                state["last_sweep_errors"] = [
                    "full sweep lacked matching build receipts and judge reproduction"
                ]
            if completed:
                state["phase"] = "judge"
                state["worktree"] = None
                save_state(self.state_path, state)
                self._append_ledger("judge", "ACCEPT", result["summary"])
                self._append_ledger("supervisor", "PROOF-COMPLETE", "Two clean sweeps accepted")
                self._cleanup_delivered_worktree(delivered_worktree, delivered_build)
                return "complete"
            self._reset_cycle(state)
            save_state(self.state_path, state)
            self._append_ledger("judge", "ACCEPT", result["summary"])
            self._cleanup_delivered_worktree(delivered_worktree, delivered_build)
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
        if phase not in ("spec", "build", "rework", "judge"):
            raise RuntimeError("unknown persisted phase: %s" % phase)
        try:
            if phase == "spec":
                return self._run_spec(state)
            if phase == "build":
                return self._run_build(state)
            if phase == "rework":
                return self._run_build(state, rework=True)
            if phase == "judge":
                return self._run_judge(state)
        except (AgentFailure, OSError, subprocess.SubprocessError, RuntimeError) as error:
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

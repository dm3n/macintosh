"""Crash-resumable spec -> build -> judge accuracy supervisor."""

import copy
import fcntl
import hashlib
import json
import os
import re
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

APPLICATION_PATHS = (
    "railz_ingestion",
    "canonical_storage",
    "classification",
    "statement_snapshot",
    "financial_calculation",
    "report_api",
    "ui",
    "export",
    "ai_output",
    "data_reconciliation",
)

PRODUCTION_PROOF_SCHEMA = {
    "type": "object",
    "required": [
        "before_mismatch_count", "after_mismatch_count", "before_skipped_count",
        "after_skipped_count", "before_denominator", "after_denominator",
        "before_evidence_ids", "after_evidence_ids", "deployment_evidence_ids",
        "candidate_commit", "deployed_commit", "deployed_at", "observed_at",
        "adjacent_regressions",
    ],
    "properties": {
        "before_mismatch_count": {"type": "integer", "minimum": 1},
        "after_mismatch_count": {"type": "integer", "minimum": 0},
        "before_skipped_count": {"type": "integer", "minimum": 0},
        "after_skipped_count": {"type": "integer", "minimum": 0},
        "before_denominator": {"type": "integer", "minimum": 1},
        "after_denominator": {"type": "integer", "minimum": 1},
        "before_evidence_ids": {
            "type": "array", "items": {"type": "string"}, "minItems": 1,
        },
        "after_evidence_ids": {
            "type": "array", "items": {"type": "string"}, "minItems": 1,
        },
        "deployment_evidence_ids": {
            "type": "array", "items": {"type": "string"}, "minItems": 1,
        },
        "candidate_commit": {"type": "string"},
        "deployed_commit": {"type": "string"},
        "deployed_at": {"type": "string"},
        "observed_at": {"type": "string"},
        "adjacent_regressions": {"type": "integer", "minimum": 0},
    },
}


SPEC_SCHEMA = {
    "type": "object",
    "required": [
        "decision", "summary", "contract", "blockers", "resolved_blocker_ids",
        "coverage_observations",
    ],
    "properties": {
        "decision": {"enum": ["code", "operations", "proof", "blocked"]},
        "summary": {"type": "string"},
        "contract": {
            "type": ["object", "null"],
            "required": [
                "id", "title", "action", "work_kind", "target_repo", "domain",
                "workspace_names", "root_cause_hypothesis", "baseline_mismatch_count",
                "target_mismatch_count", "baseline_evidence_ids", "application_paths",
                "acceptance_assertions", "verification_plan", "moves_customer_numbers",
                "depends_on_contract_id", "idempotency_key",
            ],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "action": {"enum": ["code", "operations", "proof"]},
                "work_kind": {"enum": [
                    "application_fix", "data_fix", "mismatch_proof", "full_sweep",
                ]},
                "target_repo": {"type": ["string", "null"]},
                "domain": {"enum": list(REQUIRED_DOMAINS)},
                "workspace_names": {"type": "array", "items": {"type": "string"}},
                "root_cause_hypothesis": {"type": "string"},
                "baseline_mismatch_count": {"type": "integer", "minimum": 0},
                "target_mismatch_count": {"enum": [0]},
                "baseline_evidence_ids": {
                    "type": "array", "items": {"type": "string"}, "minItems": 1,
                },
                "application_paths": {
                    "type": "array",
                    "items": {"enum": list(APPLICATION_PATHS)},
                    "minItems": 1,
                },
                "acceptance_assertions": {"type": "array", "items": {"type": "string"}},
                "verification_plan": {"type": "array", "items": {"type": "string"}},
                "moves_customer_numbers": {"type": "boolean"},
                "depends_on_contract_id": {"type": ["string", "null"]},
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
        "production_proof": PRODUCTION_PROOF_SCHEMA,
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
        "verdict": {"enum": ["ACCEPT", "CANDIDATE", "REJECT", "BLOCKED"]},
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
        "production_proof": PRODUCTION_PROOF_SCHEMA,
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
                historical_ids = list(state.get("historical_completed_contract_ids", []))
                completed_contract_ids = list(state.get("completed_contract_ids", []))
                for contract_id in self._accepted_contract_ids_from_ledger():
                    if contract_id not in historical_ids:
                        historical_ids.append(contract_id)
                for contract_id in completed_contract_ids:
                    if contract_id not in historical_ids:
                        historical_ids.append(contract_id)
                self._reset_cycle(state)
                state["completed_contract_ids"] = []
                state["historical_completed_contract_ids"] = historical_ids
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

    def _accepted_contract_ids_from_ledger(self):
        if not os.path.exists(self.ledger_path):
            return []
        accepted_ids = []
        with open(self.ledger_path) as ledger:
            for line in ledger:
                fields = [field.strip() for field in line.split("|", 3)]
                if (
                    len(fields) != 4
                    or fields[1] != "judge"
                    or fields[2] not in ("ACCEPT", "ACCURACY-ACCEPT")
                ):
                    continue
                match = re.search(r"\b(?:C\d+|ACC-[A-Za-z0-9][A-Za-z0-9-]*)\b", fields[3])
                if match and match.group(0) not in accepted_ids:
                    accepted_ids.append(match.group(0))
        return accepted_ids

    def import_delivery_candidates(self, candidates):
        """Atomically import pre-upgrade PRs that still require production proof."""
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("delivery candidate import requires a non-empty list")
        required = (
            "contract_id", "title", "target_repo", "workspace_names", "domain",
            "baseline_mismatch_count", "baseline_evidence_ids", "application_paths",
            "pr_url", "commit", "branch", "moves_customer_numbers", "status",
        )
        allowed_statuses = (
            "awaiting_review", "awaiting_production_proof", "quarantined"
        )
        normalized = []
        for raw_candidate in candidates:
            if not isinstance(raw_candidate, dict):
                raise ValueError("delivery candidate must be an object")
            missing = [field for field in required if field not in raw_candidate]
            if missing:
                raise ValueError(
                    "delivery candidate is missing: %s" % ", ".join(missing)
                )
            candidate = copy.deepcopy(raw_candidate)
            if candidate["target_repo"] not in REPOSITORIES:
                raise ValueError("delivery candidate repository is not allowlisted")
            if candidate["status"] not in allowed_statuses:
                raise ValueError("delivery candidate status is invalid")
            if candidate["domain"] not in REQUIRED_DOMAINS:
                raise ValueError("delivery candidate domain is invalid")
            candidate.setdefault("queued_at", utc_now())
            normalized.append(candidate)

        self.ensure_runtime()
        state = load_state(self.state_path)
        imported_ids = [candidate["contract_id"] for candidate in normalized]
        if len(imported_ids) != len(set(imported_ids)):
            raise ValueError("delivery candidate contract IDs must be unique")
        historical_ids = state.setdefault("historical_completed_contract_ids", [])
        for contract_id in imported_ids:
            if (
                contract_id in state.get("completed_contract_ids", [])
                and contract_id not in historical_ids
            ):
                historical_ids.append(contract_id)
        state["completed_contract_ids"] = [
            contract_id for contract_id in state.get("completed_contract_ids", [])
            if contract_id not in imported_ids
        ]
        state["delivery_candidates"] = [
            candidate for candidate in state.get("delivery_candidates", [])
            if candidate.get("contract_id") not in imported_ids
        ] + normalized
        self._reset_cycle(state)
        state["status"] = "running"
        state["clean_sweeps"] = []
        state["last_sweep_errors"] = [
            "unproved delivery backlog imported; fleet certification restarted"
        ]
        save_state(self.state_path, state)
        self._append_ledger(
            "supervisor", "BACKLOG-IMPORTED",
            "%s candidates imported; production proof required" % len(normalized),
        )

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
            "completed_contract_ids": state.get("completed_contract_ids"),
            "completed_operation_ids": state.get("completed_operation_ids"),
            "historical_completed_contract_ids": state.get(
                "historical_completed_contract_ids"
            ),
            "delivery_candidates": state.get("delivery_candidates"),
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

    def _validate_contract(self, result, state):
        work_unit = result.get("contract") or {}
        action = work_unit.get("action")
        if result.get("decision") != action:
            raise AgentFailure("spec decision and contract action disagree")
        if work_unit.get("domain") not in REQUIRED_DOMAINS:
            raise AgentFailure("spec selected an unknown accuracy domain")
        if not work_unit.get("id") or not work_unit.get("title"):
            raise AgentFailure("spec contract is missing its identity")
        if work_unit.get("id") in state.get("completed_contract_ids", []):
            raise AgentFailure("spec contract ID was already accepted and cannot be reused")
        candidates = self._pending_delivery_candidates(state)
        if any(
            item.get("contract_id") == work_unit.get("id")
            for item in state.get("delivery_candidates", [])
        ):
            raise AgentFailure("spec contract ID already belongs to a delivery candidate")
        work_kind = work_unit.get("work_kind")
        allowed_work_kinds = {
            "code": {"application_fix"},
            "operations": {"data_fix"},
            "proof": {"mismatch_proof", "full_sweep"},
        }
        if work_kind not in allowed_work_kinds.get(action, set()):
            raise AgentFailure("spec work kind does not match its action")
        baseline_mismatches = work_unit.get("baseline_mismatch_count")
        if type(baseline_mismatches) is not int or baseline_mismatches < 0:
            raise AgentFailure("spec contract has no valid baseline mismatch count")
        if work_kind != "full_sweep" and baseline_mismatches == 0:
            raise AgentFailure("ordinary work requires a positive baseline mismatch count")
        if work_unit.get("target_mismatch_count") != 0:
            raise AgentFailure("spec contract target mismatch count must be zero")
        evidence_ids = work_unit.get("baseline_evidence_ids")
        if not (
            isinstance(evidence_ids, list)
            and evidence_ids
            and all(isinstance(item, str) and item.strip() for item in evidence_ids)
        ):
            raise AgentFailure("spec contract has no baseline mismatch evidence")
        application_paths = work_unit.get("application_paths")
        if not (
            isinstance(application_paths, list)
            and application_paths
            and all(path in APPLICATION_PATHS for path in application_paths)
        ):
            raise AgentFailure("spec contract has no valid application data path")
        if not work_unit.get("acceptance_assertions") or not work_unit.get("verification_plan"):
            raise AgentFailure("spec contract has no testable assertions")
        target_repo = work_unit.get("target_repo")
        if action == "code" and target_repo not in REPOSITORIES:
            raise AgentFailure("code contract target repository is not allowlisted")
        if action in ("operations", "proof") and target_repo is not None:
            raise AgentFailure("non-code contract cannot target a repository")
        dependency = work_unit.get("depends_on_contract_id")
        if action in ("code", "operations") and dependency is not None:
            raise AgentFailure("code and operations contracts cannot depend on a candidate")
        if action in ("code", "operations") and candidates:
            raise AgentFailure(
                "a delivery candidate is already in flight; only linked production proof is allowed"
            )
        if work_kind == "full_sweep":
            if dependency is not None:
                raise AgentFailure("a full sweep cannot depend on one delivery candidate")
            if candidates:
                raise AgentFailure(
                    "a full sweep requires no pending delivery candidates"
                )
        elif work_kind == "mismatch_proof":
            candidate = self._candidate_by_id(state, dependency) if dependency else None
            if candidates and candidate is None:
                raise AgentFailure(
                    "production proof must link the in-flight delivery candidate"
                )
            if dependency and candidate is None:
                raise AgentFailure("production proof references an unknown delivery candidate")
            if candidate:
                if baseline_mismatches != candidate.get("baseline_mismatch_count"):
                    raise AgentFailure("production proof changed the candidate mismatch baseline")
                if work_unit.get("domain") != candidate.get("domain"):
                    raise AgentFailure("production proof changed the candidate domain")
                if set(work_unit.get("workspace_names", [])) != set(
                    candidate.get("workspace_names", [])
                ):
                    raise AgentFailure("production proof changed the candidate workspace scope")
                if not set(candidate.get("application_paths", [])).issubset(
                    set(application_paths)
                ):
                    raise AgentFailure("production proof omitted a candidate application path")
                if not set(candidate.get("baseline_evidence_ids", [])).issubset(
                    set(evidence_ids)
                ):
                    raise AgentFailure("production proof omitted candidate baseline evidence")
        if state.get("status") == "certified" and work_kind != "full_sweep":
            raise AgentFailure(
                "a certified loop may only run continuing full-fleet certification sweeps"
            )

    def _derive_idempotency_key(self, work_unit):
        identity = {
            key: work_unit.get(key)
            for key in (
                "id", "title", "action", "target_repo", "domain", "workspace_names",
                "work_kind", "baseline_mismatch_count", "target_mismatch_count",
                "baseline_evidence_ids", "application_paths", "acceptance_assertions",
                "verification_plan", "moves_customer_numbers",
                "depends_on_contract_id",
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

    def _pending_delivery_candidates(self, state):
        return [
            candidate for candidate in state.get("delivery_candidates", [])
            if isinstance(candidate, dict) and candidate.get("status") != "quarantined"
        ]

    def _candidate_by_id(self, state, contract_id):
        if not contract_id:
            return None
        for candidate in self._pending_delivery_candidates(state):
            if candidate.get("contract_id") == contract_id:
                return candidate
        return None

    def _judge_base_passes(self, result, verdict):
        gates = result.get("hard_gates", {})
        required_gates = (
            "contract_met", "regression_evidence", "source_reconciled", "freshness", "safety"
        )
        return (
            result.get("verdict") == verdict
            and result.get("score", 0) >= 0.90
            and all(gates.get(gate) is True for gate in required_gates)
        )

    def _build_is_ready(self, state):
        build = state.get("build_result") or {}
        return (
            build.get("outcome") == "ready_for_judge"
            and bool(build.get("evidence"))
            and bool(build.get("receipts"))
        )

    def _judge_candidate_ready(self, state, result):
        work_unit = state.get("active_contract") or {}
        build = state.get("build_result") or {}
        if (
            work_unit.get("action") != "code"
            or not self._judge_base_passes(result, "CANDIDATE")
            or not self._build_is_ready(state)
        ):
            return False
        delivery_fields = (build.get("branch"), build.get("commit"), build.get("pr_url"))
        if not all(isinstance(value, str) and value for value in delivery_fields):
            return False
        if not build.get("tests"):
            return False
        if (
            work_unit.get("moves_customer_numbers") is True
            and build.get("moves_customer_numbers") is not True
        ):
            return False
        worktree = self._worktree_from_state(state)
        return worktree is not None and self.verify_delivery_fn(
            worktree,
            build["pr_url"],
            build["commit"],
            work_unit.get("moves_customer_numbers") is True,
        )

    def _queue_delivery_candidate(self, state, work_unit, build):
        candidate = {
            "contract_id": work_unit["id"],
            "title": work_unit["title"],
            "target_repo": work_unit["target_repo"],
            "workspace_names": copy.deepcopy(work_unit["workspace_names"]),
            "domain": work_unit["domain"],
            "baseline_mismatch_count": work_unit["baseline_mismatch_count"],
            "baseline_evidence_ids": copy.deepcopy(work_unit["baseline_evidence_ids"]),
            "application_paths": copy.deepcopy(work_unit["application_paths"]),
            "pr_url": build["pr_url"],
            "commit": build["commit"],
            "branch": build["branch"],
            "moves_customer_numbers": work_unit.get("moves_customer_numbers") is True,
            "status": "awaiting_review",
            "queued_at": utc_now(),
        }
        state["delivery_candidates"] = [
            existing for existing in state.get("delivery_candidates", [])
            if existing.get("contract_id") != work_unit["id"]
        ] + [candidate]
        state["completed_contract_ids"] = [
            contract_id for contract_id in state.get("completed_contract_ids", [])
            if contract_id != work_unit["id"]
        ]

    def _parse_proof_time(self, value):
        if not isinstance(value, str) or not value:
            return None
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            return None
        return timestamp

    def _production_proof_accepts(self, state, result):
        work_unit = state.get("active_contract") or {}
        build = state.get("build_result") or {}
        proof = result.get("production_proof")
        if not isinstance(proof, dict) or build.get("production_proof") != proof:
            return False
        integer_fields = (
            "before_mismatch_count", "after_mismatch_count", "before_skipped_count",
            "after_skipped_count", "before_denominator", "after_denominator",
            "adjacent_regressions",
        )
        if any(type(proof.get(field)) is not int for field in integer_fields):
            return False
        if (
            proof["before_mismatch_count"] != work_unit.get("baseline_mismatch_count")
            or proof["before_mismatch_count"] <= 0
            or proof["after_mismatch_count"] != 0
            or proof["before_skipped_count"] < 0
            or proof["after_skipped_count"] > proof["before_skipped_count"]
            or proof["before_denominator"] <= 0
            or proof["after_denominator"] < proof["before_denominator"]
            or proof["before_mismatch_count"] > proof["before_denominator"]
            or proof["before_skipped_count"] > proof["before_denominator"]
            or proof["after_skipped_count"] > proof["after_denominator"]
            or proof["adjacent_regressions"] != 0
        ):
            return False
        evidence_fields = (
            "before_evidence_ids", "after_evidence_ids", "deployment_evidence_ids"
        )
        for field in evidence_fields:
            values = proof.get(field)
            if not (
                isinstance(values, list)
                and values
                and len(values) == len(set(values))
                and all(isinstance(value, str) and value.strip() for value in values)
            ):
                return False
        before_ids = set(proof["before_evidence_ids"])
        after_ids = set(proof["after_evidence_ids"])
        deployment_ids = set(proof["deployment_evidence_ids"])
        if before_ids & after_ids or before_ids & deployment_ids or after_ids & deployment_ids:
            return False
        if not set(work_unit.get("baseline_evidence_ids", [])).issubset(before_ids):
            return False
        deployed_at = self._parse_proof_time(proof.get("deployed_at"))
        observed_at = self._parse_proof_time(proof.get("observed_at"))
        if (
            deployed_at is None
            or observed_at is None
            or observed_at < deployed_at
            or observed_at > datetime.now(timezone.utc)
        ):
            return False
        if not all(
            isinstance(proof.get(field), str) and proof[field].strip()
            for field in ("candidate_commit", "deployed_commit")
        ):
            return False
        candidate = self._candidate_by_id(
            state, work_unit.get("depends_on_contract_id")
        )
        if candidate and proof["candidate_commit"] != candidate.get("commit"):
            return False
        required_ids = before_ids | after_ids | deployment_ids
        receipt_ids = {
            receipt.get("id") for receipt in build.get("receipts", [])
            if receipt.get("status") == "complete"
        }
        judge_ids = set(result.get("verified_evidence", []))
        return required_ids.issubset(receipt_ids) and required_ids.issubset(judge_ids)

    def _judge_accepts(self, state, result):
        if not self._judge_base_passes(result, "ACCEPT") or not self._build_is_ready(state):
            return False
        work_unit = state.get("active_contract") or {}
        work_kind = work_unit.get("work_kind")
        if work_kind == "mismatch_proof":
            return self._production_proof_accepts(state, result)
        if work_kind != "full_sweep":
            return False
        full_sweep = result.get("full_sweep")
        return isinstance(full_sweep, dict) and self._full_sweep_is_corroborated(
            state, full_sweep, result
        )

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

    def _record_completed_contract(self, state, contract_id):
        completed_contract_ids = state.setdefault("completed_contract_ids", [])
        if contract_id not in completed_contract_ids:
            completed_contract_ids.append(contract_id)

    def _revoke_certification(self, state, reason):
        if state.get("status") != "certified":
            return
        state["status"] = "running"
        state["clean_sweeps"] = []
        state["last_sweep_errors"] = [reason]

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
        if result.get("decision") == "blocked":
            if result.get("contract") is not None or not result.get("blockers"):
                raise AgentFailure("blocked spec requires a null contract and explicit blocker")
            self._revoke_certification(
                state, "continuing fleet certification was blocked"
            )
            state["cycle"] += 1
            self._reconcile_blockers(state, result)
            self._reset_cycle(state, 300)
            save_state(self.state_path, state)
            self._append_ledger("spec", "DEPLOY-BLOCKED", result["summary"])
            return "retry"
        self._validate_contract(result, state)
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
        if (
            state["active_contract"].get("work_kind") == "full_sweep"
            and result.get("outcome") != "ready_for_judge"
        ):
            self._revoke_certification(
                state, "continuing full-fleet sweep did not produce judge-ready evidence"
            )
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
        work_unit = state["active_contract"]
        delivered_worktree = self._worktree_from_state(state)
        delivered_build = state.get("build_result") or {}

        if self._judge_candidate_ready(state, result):
            self._queue_delivery_candidate(state, work_unit, delivered_build)
            self._resolve_accepted_blockers(state, result)
            self._reset_cycle(state)
            save_state(self.state_path, state)
            self._append_ledger(
                "judge", "CANDIDATE-READY", "%s: %s" % (work_unit["id"], result["summary"])
            )
            self._cleanup_delivered_worktree(delivered_worktree, delivered_build)
            return "spec"

        if work_unit.get("action") == "operations" and self._judge_base_passes(
            result, "ACCEPT"
        ) and self._build_is_ready(state):
            completed_operation_ids = state.setdefault("completed_operation_ids", [])
            if work_unit["id"] not in completed_operation_ids:
                completed_operation_ids.append(work_unit["id"])
            self._resolve_accepted_blockers(state, result)
            self._reset_cycle(state)
            save_state(self.state_path, state)
            self._append_ledger(
                "judge", "COORDINATED", "%s: %s" % (work_unit["id"], result["summary"])
            )
            return "spec"

        accepted = self._judge_accepts(state, result)
        if accepted:
            self._record_completed_contract(state, work_unit["id"])
            dependency = work_unit.get("depends_on_contract_id")
            if dependency:
                self._record_completed_contract(state, dependency)
                state["delivery_candidates"] = [
                    candidate for candidate in state.get("delivery_candidates", [])
                    if candidate.get("contract_id") != dependency
                ]
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
                self._reset_cycle(state, 60)
                save_state(self.state_path, state)
                self._append_ledger(
                    "judge", "ACCURACY-ACCEPT",
                    "%s: %s" % (work_unit["id"], result["summary"])
                )
                self._append_ledger(
                    "supervisor", "CERTIFIED",
                    "Two clean dynamic-roster sweeps accepted; continuous monitoring remains active"
                )
                self._cleanup_delivered_worktree(delivered_worktree, delivered_build)
                return "retry"
            self._reset_cycle(state)
            save_state(self.state_path, state)
            self._append_ledger(
                "judge", "ACCURACY-ACCEPT",
                "%s: %s" % (work_unit["id"], result["summary"])
            )
            self._cleanup_delivered_worktree(delivered_worktree, delivered_build)
            return "spec"

        if work_unit.get("work_kind") == "full_sweep":
            self._revoke_certification(
                state, "continuing full-fleet sweep was not independently corroborated"
            )
            state["last_sweep_errors"] = [
                "full sweep lacked matching build receipts and judge reproduction"
            ]

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
            self._revoke_certification(
                state, "continuing certification could not obtain valid evidence"
            )
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
            remaining = self._seconds_until_retry(state)
            if remaining:
                self.sleep_fn(min(5, remaining))
                continue
            outcome = self.step()
        self._append_ledger("supervisor", "STOP", "Signal received; resumable state saved")
        return 0

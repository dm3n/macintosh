import copy
import os
import sys
import tempfile
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.claude import AgentFailure  # noqa: E402
from accuracy_loop.model import REQUIRED_DOMAINS, load_state, save_state  # noqa: E402
from accuracy_loop.supervisor import Supervisor  # noqa: E402
from accuracy_loop.workspace import Worktree  # noqa: E402
from tests.test_model import complete_sweep  # noqa: E402


def contract(action="proof"):
    work_kind = {
        "code": "application_fix",
        "operations": "data_fix",
        "proof": "mismatch_proof",
    }[action]
    return {
        "id": "ACC-100",
        "title": "Prove report parity",
        "action": action,
        "work_kind": work_kind,
        "target_repo": "Mitch-be" if action == "code" else None,
        "domain": "api_ui_and_export_parity",
        "workspace_names": ["FusionTek (ws129)"],
        "root_cause_hypothesis": "The served surface may not share one source.",
        "baseline_mismatch_count": 1,
        "target_mismatch_count": 0,
        "baseline_evidence_ids": ["verify-fixture:before"],
        "application_paths": ["report_api"],
        "acceptance_assertions": ["All compared surfaces match exactly."],
        "verification_plan": ["Collect fresh source and served values."],
        "moves_customer_numbers": False,
        "depends_on_contract_id": None,
        "idempotency_key": "accuracy:ACC-100",
    }


def spec_result(action="proof"):
    return {
        "decision": action,
        "summary": "One bounded unit selected.",
        "contract": contract(action),
        "blockers": [],
        "resolved_blocker_ids": [],
        "coverage_observations": {},
    }


def full_sweep_spec(contract_id="ACC-SWEEP-1"):
    result = spec_result("proof")
    result["contract"].update({
        "id": contract_id,
        "title": "Run a full application accuracy sweep",
        "work_kind": "full_sweep",
        "baseline_mismatch_count": 0,
        "baseline_evidence_ids": ["fleet-zero:before-sweep"],
        "application_paths": [
            "railz_ingestion", "canonical_storage", "classification",
            "statement_snapshot", "financial_calculation", "report_api", "ui",
            "export", "ai_output", "data_reconciliation",
        ],
    })
    return result


def build_result(full_sweep=None):
    result = {
        "outcome": "ready_for_judge",
        "summary": "Evidence collected.",
        "branch": None,
        "commit": None,
        "pr_url": None,
        "ticket_urls": [],
        "tests": ["fixture check passed"],
        "evidence": ["fixture:evidence"],
        "receipts": [{
            "kind": "verification_run",
            "id": "verify-fixture",
            "url": None,
            "status": "complete",
        }],
        "moves_customer_numbers": False,
        "wait_seconds": 0,
    }
    if full_sweep is not None:
        result["full_sweep"] = full_sweep
        result["receipts"] = proof_receipts(full_sweep)
    return result


def proof_ids(sweep):
    identities = {sweep["authoritative_roster"]["id"]}
    identities.update(
        item["verification_id"]
        for item in sweep["workspace_roster"] if item["lifecycle"] == "active"
    )
    evidence_lists = [proof["evidence"] for proof in sweep["domains"].values()]
    evidence_lists.extend(sweep["scope"][key]["evidence"] for key in (
        "periods", "layers", "dimensions",
    ))
    evidence_lists.extend(
        proof["evidence"] for proof in sweep["scope"]["surfaces"].values()
    )
    for evidence in evidence_lists:
        identities.update(item["id"] for item in evidence)
    return identities


def proof_receipts(sweep):
    return [
        {"kind": "other", "id": identity, "url": None, "status": "complete"}
        for identity in sorted(proof_ids(sweep))
    ]


def delivered_code_result():
    result = build_result()
    result.update({
        "branch": "agent/accuracy-acc-100-prove-report-parity",
        "commit": "0123456789abcdef",
        "pr_url": "https://github.com/dm3n/Mitch-be/pull/9999",
        "receipts": [{
            "kind": "pull_request",
            "id": "9999",
            "url": "https://github.com/dm3n/Mitch-be/pull/9999",
            "status": "open",
        }],
    })
    return result


def production_proof(**overrides):
    proof = {
        "before_mismatch_count": 1,
        "after_mismatch_count": 0,
        "before_skipped_count": 0,
        "after_skipped_count": 0,
        "before_denominator": 12,
        "after_denominator": 12,
        "before_evidence_ids": ["verify-fixture:before"],
        "after_evidence_ids": ["verify-fixture:after"],
        "deployment_evidence_ids": ["deploy-fixture:receipt"],
        "candidate_commit": "0123456789abcdef",
        "deployed_commit": "fedcba9876543210",
        "deployed_at": "2026-08-08T16:00:00Z",
        "observed_at": "2026-08-08T16:05:00Z",
        "adjacent_regressions": 0,
    }
    proof.update(overrides)
    return proof


def proof_build_result(proof=None):
    proof = proof or production_proof()
    result = build_result()
    result["production_proof"] = proof
    result["receipts"] = [
        {"kind": "verification_run", "id": evidence_id, "url": None, "status": "complete"}
        for evidence_id in (
            proof["before_evidence_ids"]
            + proof["after_evidence_ids"]
            + proof["deployment_evidence_ids"]
        )
    ]
    return result


def judge_result(verdict="ACCEPT", full_sweep=None):
    passing = verdict in ("ACCEPT", "CANDIDATE")
    result = {
        "verdict": verdict,
        "score": 0.96 if passing else 0.5,
        "summary": "Independent fixture verdict.",
        "hard_gates": {
            "contract_met": passing,
            "regression_evidence": passing,
            "source_reconciled": passing,
            "freshness": passing,
            "safety": True,
        },
        "findings": [] if passing else ["Evidence is incomplete."],
        "rework_instructions": [] if passing else ["Collect the missing evidence."],
        "verified_evidence": ["judge:evidence"],
        "coverage_updates": {},
        "blockers": [],
        "resolved_blocker_ids": [],
        "wait_seconds": 0,
    }
    if full_sweep is not None:
        result["full_sweep"] = full_sweep
        result["verified_evidence"] = sorted(proof_ids(full_sweep))
    return result


def proof_judge_result(proof=None):
    proof = proof or production_proof()
    result = judge_result("ACCEPT")
    result["production_proof"] = proof
    result["verified_evidence"] = sorted(
        proof["before_evidence_ids"]
        + proof["after_evidence_ids"]
        + proof["deployment_evidence_ids"]
    )
    return result


def candidate_record(**overrides):
    result = {
        "contract_id": "ACC-CANDIDATE",
        "title": "Fix report parity",
        "target_repo": "Mitch-be",
        "workspace_names": ["FusionTek (ws129)"],
        "domain": "api_ui_and_export_parity",
        "baseline_mismatch_count": 1,
        "baseline_evidence_ids": ["verify-fixture:before"],
        "application_paths": ["report_api"],
        "pr_url": "https://github.com/dm3n/Mitch-be/pull/9999",
        "commit": "0123456789abcdef",
        "branch": "agent/accuracy-acc-candidate",
        "moves_customer_numbers": False,
        "status": "awaiting_production_proof",
        "queued_at": "2026-08-08T15:00:00Z",
    }
    result.update(overrides)
    return result


class ScriptedRunner:
    def __init__(self, results):
        self.results = list(results)
        self.phases = []
        self.prompts = []
        self.capability_phases = []
        self.active_process = None

    def run(self, phase, prompt, schema, cwd, capability_phase=None):
        self.phases.append(phase)
        self.capability_phases.append(capability_phase)
        self.prompts.append(prompt)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return copy.deepcopy(result)

    def terminate(self):
        self.active_process = None


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = self.temporary.name
        self.runtime = os.path.join(self.root, "runtime")
        self.source = os.path.join(self.root, "source")
        self.finsider = os.path.join(self.root, "finsider")
        os.makedirs(os.path.join(self.source, "prompts"))
        os.makedirs(self.finsider)
        with open(os.path.join(self.source, "contract.md"), "w") as contract_file:
            contract_file.write("# Contract\n")
        for phase in ("spec", "build", "judge"):
            with open(os.path.join(self.source, "prompts", phase + ".md"), "w") as prompt_file:
                prompt_file.write("%s phase\n" % phase)
        self.fake_worktree_path = os.path.join(self.root, "worktree")
        os.makedirs(self.fake_worktree_path)
        self.fake_worktree = Worktree(
            "Mitch-be",
            os.path.join(self.finsider, "Mitch-be"),
            "development",
            "agent/accuracy-acc-100",
            self.fake_worktree_path,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def supervisor(self, results):
        runner = ScriptedRunner(results)
        supervisor = Supervisor(
            runtime_dir=self.runtime,
            source_dir=self.source,
            finsider_dir=self.finsider,
            runner=runner,
            create_worktree_fn=lambda *args, **kwargs: self.fake_worktree,
            remove_worktree_fn=lambda *args, **kwargs: True,
            verify_delivery_fn=lambda *args, **kwargs: True,
            sleep_fn=lambda seconds: None,
        )
        return supervisor, runner

    def test_runtime_initialization_has_exactly_three_durable_state_files(self):
        supervisor, _ = self.supervisor([])

        supervisor.ensure_runtime()

        files = sorted(
            name for name in os.listdir(self.runtime)
            if os.path.isfile(os.path.join(self.runtime, name))
        )
        self.assertEqual(files, ["CONTRACT.md", "LEDGER.md", "STATE.json"])

    def test_contract_update_is_atomic_and_restarts_proof_sequence(self):
        supervisor, _ = self.supervisor([])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        preserved_coverage = copy.deepcopy(state["coverage"])
        preserved_blockers = [{
            "id": "ACC-BLOCKED",
            "summary": "A real mismatch remains.",
            "owner": "Accuracy",
            "evidence_needed": ["A zero-mismatch rerun."],
        }]
        state["phase"] = "build"
        state["cycle"] = 25
        state["phase_attempts"] = 7
        state["retry_at"] = "2026-08-07T18:36:41Z"
        state["active_contract"] = contract("code")
        state["spec_result"] = spec_result("code")
        state["build_result"] = build_result()
        state["judge_result"] = judge_result("REJECT")
        state["action_intent"] = {
            "idempotency_key": "finsider-accuracy:ACC-100:stale",
            "started_at": "2026-08-07T18:00:00Z",
            "receipts": [],
        }
        state["worktree"] = self.fake_worktree.to_dict()
        state["rework_count"] = 1
        state["last_error"] = "existing worktree has unexpected branch"
        state["blockers"] = preserved_blockers
        state["clean_sweeps"] = [{"sweep_id": "old"}]
        state["status"] = "complete"
        save_state(supervisor.state_path, state)
        with open(os.path.join(self.source, "contract.md"), "w") as contract_file:
            contract_file.write("# Contract v2\n")

        supervisor.ensure_runtime()

        state = load_state(supervisor.state_path)
        with open(supervisor.contract_path) as contract_file:
            self.assertEqual(contract_file.read(), "# Contract v2\n")
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(state["phase"], "spec")
        self.assertEqual(state["cycle"], 25)
        self.assertEqual(state["phase_attempts"], 0)
        self.assertIsNone(state["retry_at"])
        self.assertIsNone(state["active_contract"])
        self.assertIsNone(state["spec_result"])
        self.assertIsNone(state["build_result"])
        self.assertIsNone(state["judge_result"])
        self.assertIsNone(state["action_intent"])
        self.assertIsNone(state["worktree"])
        self.assertEqual(state["rework_count"], 0)
        self.assertIsNone(state["last_error"])
        self.assertEqual(state["coverage"], preserved_coverage)
        self.assertEqual(state["blockers"], preserved_blockers)
        self.assertFalse(os.path.exists(supervisor.contract_path + ".tmp"))

    def test_contract_update_does_not_recover_legacy_accept_as_accuracy(self):
        supervisor, _ = self.supervisor([])
        supervisor.ensure_runtime()
        with open(supervisor.ledger_path, "a") as ledger:
            ledger.write(
                "- 2026-08-07T18:00:00Z | judge | ACCEPT | C51 widened flux decimals\n"
            )
        with open(os.path.join(self.source, "contract.md"), "w") as contract_file:
            contract_file.write("# Contract v2\n")

        supervisor.ensure_runtime()

        state = load_state(supervisor.state_path)
        self.assertNotIn("C51", state["completed_contract_ids"])
        self.assertIn("C51", state["historical_completed_contract_ids"])

    def test_accepted_work_starts_next_spec_without_schedule_sleep(self):
        next_result = spec_result("proof")
        next_result["contract"]["id"] = "ACC-101"
        supervisor, runner = self.supervisor(
            [spec_result("proof"), proof_build_result(), proof_judge_result(), next_result]
        )

        supervisor.step()
        supervisor.step()
        supervisor.step()
        supervisor.step()

        self.assertEqual(runner.phases, ["spec", "build", "judge", "spec"])
        self.assertEqual(load_state(supervisor.state_path)["phase"], "build")

    def test_accepted_work_records_its_contract_id_once(self):
        supervisor, _ = self.supervisor(
            [spec_result("proof"), proof_build_result(), proof_judge_result()]
        )

        supervisor.step()
        supervisor.step()
        supervisor.step()

        self.assertEqual(
            load_state(supervisor.state_path)["completed_contract_ids"],
            ["ACC-100"],
        )

    def test_code_action_creates_worktree_before_build(self):
        supervisor, runner = self.supervisor([spec_result("code"), build_result()])

        supervisor.step()
        supervisor.step()

        self.assertEqual(runner.phases, ["spec", "build"])
        self.assertEqual(runner.capability_phases, [None, "code"])
        self.assertEqual(load_state(supervisor.state_path)["worktree"]["path"],
                         self.fake_worktree_path)

    def test_invalid_code_contract_retries_spec_without_crashing(self):
        invalid = spec_result("code")
        invalid["contract"]["target_repo"] = None
        supervisor, runner = self.supervisor([invalid])

        outcome = supervisor.step()

        self.assertEqual(outcome, "retry")
        self.assertEqual(runner.phases, ["spec"])
        self.assertEqual(load_state(supervisor.state_path)["phase"], "spec")

    def test_spec_rejects_a_completed_contract_id(self):
        supervisor, runner = self.supervisor([spec_result("proof")])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["completed_contract_ids"] = ["ACC-100"]
        save_state(supervisor.state_path, state)

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertEqual(runner.phases, ["spec"])
        self.assertEqual(state["phase"], "spec")
        self.assertIn("already accepted", state["last_error"])

    def test_spec_rejects_coverage_only_work_without_a_baseline_mismatch(self):
        result = spec_result("code")
        result["contract"]["baseline_mismatch_count"] = 0
        supervisor, _ = self.supervisor([result])

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertEqual(state["phase"], "spec")
        self.assertIn("positive baseline mismatch", state["last_error"])

    def test_spec_rejects_work_without_an_application_data_path(self):
        result = spec_result("code")
        result["contract"]["application_paths"] = []
        supervisor, _ = self.supervisor([result])

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertEqual(state["phase"], "spec")
        self.assertIn("application data path", state["last_error"])

    def test_judge_cannot_accept_code_that_has_no_pr_handoff(self):
        supervisor, runner = self.supervisor(
            [spec_result("code"), build_result(), judge_result("ACCEPT")]
        )

        supervisor.step()
        supervisor.step()
        supervisor.step()

        self.assertEqual(runner.phases, ["spec", "build", "judge"])
        self.assertEqual(load_state(supervisor.state_path)["phase"], "rework")

    def test_candidate_state_is_persisted_before_delivered_worktree_cleanup(self):
        observed_states = []
        runner = ScriptedRunner(
            [spec_result("code"), delivered_code_result(), judge_result("CANDIDATE")]
        )
        supervisor = Supervisor(
            runtime_dir=self.runtime,
            source_dir=self.source,
            finsider_dir=self.finsider,
            runner=runner,
            create_worktree_fn=lambda *args, **kwargs: self.fake_worktree,
            remove_worktree_fn=lambda *args, **kwargs: observed_states.append(
                load_state(supervisor.state_path)
            ) or True,
            verify_delivery_fn=lambda *args, **kwargs: True,
            sleep_fn=lambda seconds: None,
        )

        supervisor.step()
        supervisor.step()
        supervisor.step()

        self.assertEqual(len(observed_states), 1)
        self.assertEqual(observed_states[0]["phase"], "spec")
        self.assertIsNone(observed_states[0]["worktree"])
        self.assertEqual(observed_states[0]["completed_contract_ids"], [])
        self.assertEqual(
            observed_states[0]["delivery_candidates"][0]["contract_id"],
            "ACC-100",
        )

    def test_restart_resumes_recorded_judge_phase(self):
        supervisor, runner = self.supervisor([judge_result("BLOCKED")])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["phase"] = "judge"
        state["active_contract"] = contract("proof")
        state["build_result"] = build_result()
        save_state(supervisor.state_path, state)

        supervisor.step()

        self.assertEqual(runner.phases, ["judge"])
        self.assertEqual(load_state(supervisor.state_path)["phase"], "spec")

    def test_code_rejection_gets_only_one_rework(self):
        supervisor, runner = self.supervisor(
            [
                spec_result("code"),
                build_result(),
                judge_result("REJECT"),
                build_result(),
                judge_result("REJECT"),
            ]
        )

        for _ in range(5):
            supervisor.step()

        self.assertEqual(runner.phases, ["spec", "build", "judge", "rework", "judge"])
        state = load_state(supervisor.state_path)
        self.assertEqual(state["phase"], "spec")
        self.assertTrue(state["blockers"])

    def test_two_accepted_full_sweeps_certify_but_keep_loop_alive(self):
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        supervisor, _ = self.supervisor(
            [
                full_sweep_spec("ACC-SWEEP-1"),
                build_result(first),
                judge_result("ACCEPT", first),
                full_sweep_spec("ACC-SWEEP-2"),
                build_result(second),
                judge_result("ACCEPT", second),
            ]
        )

        for _ in range(6):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["status"], "certified")
        self.assertEqual(len(state["clean_sweeps"]), 2)
        self.assertEqual(state["phase"], "spec")
        self.assertIsNotNone(state["retry_at"])

    def test_certified_loop_only_allows_continuing_full_fleet_sweeps(self):
        supervisor, runner = self.supervisor([full_sweep_spec("ACC-SWEEP-3")])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["status"] = "certified"
        save_state(supervisor.state_path, state)

        outcome = supervisor.step()

        self.assertEqual(outcome, "build")
        self.assertEqual(runner.phases, ["spec"])
        self.assertEqual(load_state(supervisor.state_path)["status"], "certified")

    def test_certified_loop_rejects_an_ordinary_work_unit(self):
        supervisor, _ = self.supervisor([spec_result("proof")])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["status"] = "certified"
        save_state(supervisor.state_path, state)

        outcome = supervisor.step()

        self.assertEqual(outcome, "retry")
        self.assertIn(
            "continuing full-fleet", load_state(supervisor.state_path)["last_error"]
        )

    def test_failed_continuing_sweep_revokes_certification(self):
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        supervisor, _ = self.supervisor([
            full_sweep_spec("ACC-SWEEP-1"),
            build_result(first),
            judge_result("ACCEPT", first),
            full_sweep_spec("ACC-SWEEP-2"),
            build_result(second),
            judge_result("ACCEPT", second),
            full_sweep_spec("ACC-SWEEP-3"),
            build_result(),
            judge_result("ACCEPT"),
        ])

        for _ in range(9):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["clean_sweeps"], [])

    def test_full_sweep_without_matching_receipts_cannot_complete(self):
        sweep = complete_sweep("sweep-1")
        build = build_result(sweep)
        build["receipts"] = [{
            "kind": "verification_run", "id": "not-the-proof", "url": None,
            "status": "complete",
        }]
        supervisor, _ = self.supervisor([
            full_sweep_spec(), build, judge_result("ACCEPT", sweep),
        ])

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(
            state["last_sweep_errors"],
            ["full sweep lacked matching build receipts and judge reproduction"],
        )

    def test_corroborated_full_sweep_can_directly_resolve_prior_blocker(self):
        sweep = complete_sweep("sweep-resolves-blocker")
        verdict = judge_result("ACCEPT", sweep)
        verdict["resolved_blocker_ids"] = ["ACC-OLD"]
        supervisor, _ = self.supervisor([
            full_sweep_spec(), build_result(sweep), verdict,
        ])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["blockers"] = [{
            "id": "ACC-OLD",
            "summary": "A previously observed mismatch.",
            "owner": "Accuracy",
            "evidence_needed": ["A complete fresh zero-mismatch sweep."],
        }]
        save_state(supervisor.state_path, state)

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["blockers"], [])
        self.assertEqual(len(state["clean_sweeps"]), 1)

    def test_agent_failure_keeps_same_phase_and_sets_retry(self):
        supervisor, runner = self.supervisor([AgentFailure("rate limit", transient=True)])

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertEqual(runner.phases, ["spec"])
        self.assertEqual(state["phase"], "spec")
        self.assertEqual(state["phase_attempts"], 1)
        self.assertIsNotNone(state["retry_at"])

    def test_spec_replaces_agent_idempotency_key_with_deterministic_key(self):
        result = spec_result("proof")
        result["contract"]["idempotency_key"] = "agent-chosen-random-value"
        supervisor, _ = self.supervisor([result])

        supervisor.step()
        first = load_state(supervisor.state_path)["active_contract"]["idempotency_key"]

        self.assertTrue(first.startswith("finsider-accuracy:ACC-100:"))
        self.assertNotEqual(first, "agent-chosen-random-value")

    def test_waiting_build_keeps_phase_receipt_and_contract_for_polling(self):
        waiting = build_result()
        waiting.update({
            "outcome": "blocked",
            "summary": "Verification run is still in flight.",
            "wait_seconds": 60,
            "receipts": [{
                "kind": "verification_run",
                "id": "run-123",
                "url": None,
                "status": "running",
            }],
        })
        supervisor, runner = self.supervisor([spec_result("proof"), waiting])

        supervisor.step()
        key_before = load_state(supervisor.state_path)["active_contract"]["idempotency_key"]
        outcome = supervisor.step()
        state = load_state(supervisor.state_path)

        self.assertEqual(outcome, "retry")
        self.assertEqual(state["phase"], "build")
        self.assertEqual(state["active_contract"]["idempotency_key"], key_before)
        self.assertEqual(state["action_intent"]["receipts"][0]["id"], "run-123")
        self.assertIn("run-123", supervisor._render_prompt("build", state))
        self.assertEqual(runner.phases, ["spec", "build"])

    def test_restart_keeps_action_intent_before_replaying_build(self):
        supervisor, runner = self.supervisor([build_result()])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["phase"] = "build"
        state["active_contract"] = contract("proof")
        state["active_contract"]["idempotency_key"] = "finsider-accuracy:ACC-100:stable"
        state["action_intent"] = {
            "idempotency_key": "finsider-accuracy:ACC-100:stable",
            "started_at": "2026-08-06T22:00:00Z",
            "receipts": [],
        }
        save_state(supervisor.state_path, state)

        supervisor.step()

        self.assertEqual(runner.phases, ["build"])
        self.assertIn("finsider-accuracy:ACC-100:stable", runner.prompts[0])

    def test_spec_reconciles_resolved_blockers_by_stable_id(self):
        result = spec_result("proof")
        result["resolved_blocker_ids"] = ["ACC-OLD"]
        supervisor, _ = self.supervisor([result])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["blockers"] = [
            {"id": "ACC-OLD", "summary": "Old", "owner": "Ops", "evidence_needed": ["sync"]},
            {"id": "ACC-KEEP", "summary": "Keep", "owner": "Eng", "evidence_needed": ["fix"]},
        ]
        save_state(supervisor.state_path, state)

        supervisor.step()

        self.assertEqual(
            [item["id"] for item in load_state(supervisor.state_path)["blockers"]],
            ["ACC-KEEP"],
        )

    def test_accepted_judge_can_resolve_a_named_existing_blocker(self):
        verdict = proof_judge_result()
        verdict["resolved_blocker_ids"] = ["ACC-OLD"]
        supervisor, _ = self.supervisor([spec_result("proof"), proof_build_result(), verdict])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["blockers"] = [
            {"id": "ACC-OLD", "summary": "Old", "owner": "Ops", "evidence_needed": ["sync"]}
        ]
        save_state(supervisor.state_path, state)

        for _ in range(3):
            supervisor.step()

        self.assertEqual(load_state(supervisor.state_path)["blockers"], [])

    def test_open_code_pr_cannot_enter_completed_accuracy_contracts(self):
        supervisor, _ = self.supervisor([
            spec_result("code"), delivered_code_result(), judge_result("ACCEPT"),
        ])

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_candidate_verdict_queues_delivered_pr_without_claiming_accuracy(self):
        supervisor, _ = self.supervisor([
            spec_result("code"), delivered_code_result(), judge_result("CANDIDATE"),
        ])

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["phase"], "spec")
        self.assertEqual(state["completed_contract_ids"], [])
        self.assertEqual(len(state["delivery_candidates"]), 1)
        self.assertEqual(state["delivery_candidates"][0]["contract_id"], "ACC-100")

    def _run_proof(self, proof=None, judge_proof=None, candidate=None):
        proof = proof or production_proof()
        judge_proof = proof if judge_proof is None else judge_proof
        result = spec_result("proof")
        if candidate:
            result["contract"]["depends_on_contract_id"] = candidate["contract_id"]
        supervisor, _ = self.supervisor([
            result, proof_build_result(proof), proof_judge_result(judge_proof),
        ])
        supervisor.ensure_runtime()
        if candidate:
            state = load_state(supervisor.state_path)
            state["delivery_candidates"] = [candidate]
            save_state(supervisor.state_path, state)
        for _ in range(3):
            supervisor.step()
        return load_state(supervisor.state_path)

    def test_mismatch_proof_requires_structured_production_proof(self):
        supervisor, _ = self.supervisor([
            spec_result("proof"), build_result(), judge_result("ACCEPT"),
        ])

        for _ in range(3):
            supervisor.step()

        self.assertNotIn(
            "ACC-100", load_state(supervisor.state_path)["completed_contract_ids"]
        )

    def test_production_proof_rejects_residual_mismatches(self):
        state = self._run_proof(production_proof(after_mismatch_count=1))
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_production_proof_rejects_increased_skips(self):
        state = self._run_proof(production_proof(after_skipped_count=1))
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_production_proof_rejects_shrunken_denominator(self):
        state = self._run_proof(production_proof(after_denominator=11))
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_production_proof_rejects_reused_before_evidence(self):
        state = self._run_proof(production_proof(
            after_evidence_ids=["verify-fixture:before"],
        ))
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_production_proof_rejects_adjacent_regressions(self):
        state = self._run_proof(production_proof(adjacent_regressions=1))
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_production_proof_rejects_impossible_skip_denominator(self):
        state = self._run_proof(production_proof(before_skipped_count=13))
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_production_proof_must_be_independently_reproduced(self):
        build_proof = production_proof()
        judge_proof = production_proof(after_denominator=13)
        state = self._run_proof(build_proof, judge_proof)
        self.assertNotIn("ACC-100", state["completed_contract_ids"])

    def test_linked_zero_proof_closes_candidate_and_both_contract_ids(self):
        candidate = candidate_record()

        state = self._run_proof(candidate=candidate)

        self.assertEqual(state["delivery_candidates"], [])
        self.assertEqual(
            state["completed_contract_ids"], ["ACC-100", "ACC-CANDIDATE"]
        )

    def test_spec_rejects_new_code_while_delivery_candidate_exists(self):
        supervisor, _ = self.supervisor([spec_result("code")])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["delivery_candidates"] = [candidate_record()]
        save_state(supervisor.state_path, state)

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertIn("delivery candidate", state["last_error"])

    def test_linked_proof_cannot_change_candidate_workspace_scope(self):
        result = spec_result("proof")
        result["contract"]["depends_on_contract_id"] = "ACC-CANDIDATE"
        supervisor, _ = self.supervisor([result])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["delivery_candidates"] = [candidate_record(
            workspace_names=["Mizrahi Enterprises (ws162)"],
        )]
        save_state(supervisor.state_path, state)

        outcome = supervisor.step()

        self.assertEqual(outcome, "retry")
        self.assertIn("candidate workspace scope", load_state(
            supervisor.state_path
        )["last_error"])

    def test_imported_delivery_backlog_archives_false_completion_and_quarantine(self):
        supervisor, _ = self.supervisor([])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["completed_contract_ids"] = ["ACC-CANDIDATE", "ACC-UNSAFE"]
        save_state(supervisor.state_path, state)

        supervisor.import_delivery_candidates([
            candidate_record(),
            candidate_record(
                contract_id="ACC-UNSAFE", status="quarantined",
                pr_url="https://github.com/dm3n/Mitch-be/pull/1130",
            ),
        ])

        state = load_state(supervisor.state_path)
        self.assertEqual(state["completed_contract_ids"], [])
        self.assertEqual(
            state["historical_completed_contract_ids"],
            ["ACC-CANDIDATE", "ACC-UNSAFE"],
        )
        self.assertEqual(len(state["delivery_candidates"]), 2)
        self.assertEqual(len(supervisor._pending_delivery_candidates(state)), 1)

    def test_structured_blocked_spec_creates_no_work_unit_or_artifact(self):
        blocked = {
            "decision": "blocked",
            "summary": "Candidate is awaiting authorized production deployment.",
            "contract": None,
            "blockers": [{
                "id": "DEPLOY-ACC-CANDIDATE",
                "summary": "Production deployment has not happened.",
                "owner": "Finsider release owner",
                "evidence_needed": ["Authorized deployment receipt."],
            }],
            "resolved_blocker_ids": [],
            "coverage_observations": {},
        }
        supervisor, runner = self.supervisor([blocked])

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertEqual(runner.phases, ["spec"])
        self.assertEqual(state["phase"], "spec")
        self.assertIsNone(state["active_contract"])
        self.assertIsNone(state["build_result"])
        self.assertEqual(state["completed_contract_ids"], [])

    def test_operations_acceptance_is_coordination_not_accuracy(self):
        supervisor, _ = self.supervisor([
            spec_result("operations"), build_result(), judge_result("ACCEPT"),
        ])

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["completed_contract_ids"], [])
        self.assertEqual(state["completed_operation_ids"], ["ACC-100"])

    def test_full_sweep_cannot_complete_without_corroborated_sweep_object(self):
        supervisor, _ = self.supervisor([
            full_sweep_spec(), build_result(), judge_result("ACCEPT"),
        ])

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["completed_contract_ids"], [])
        self.assertEqual(state["clean_sweeps"], [])

    def test_operational_runtime_error_retries_same_phase(self):
        runner = ScriptedRunner([spec_result("code")])
        supervisor = Supervisor(
            runtime_dir=self.runtime,
            source_dir=self.source,
            finsider_dir=self.finsider,
            runner=runner,
            create_worktree_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
                RuntimeError("git fetch failed")
            ),
            remove_worktree_fn=lambda *args, **kwargs: True,
            verify_delivery_fn=lambda *args, **kwargs: True,
            sleep_fn=lambda seconds: None,
        )

        supervisor.step()
        outcome = supervisor.step()

        self.assertEqual(outcome, "retry")
        self.assertEqual(load_state(supervisor.state_path)["phase"], "build")


if __name__ == "__main__":
    unittest.main()

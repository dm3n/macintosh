import copy
import os
import sys
import tempfile
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.claude import AgentFailure  # noqa: E402
from accuracy_loop.model import REQUIRED_DOMAINS, load_state, new_state, save_state  # noqa: E402
from accuracy_loop.supervisor import Supervisor  # noqa: E402
from accuracy_loop.workspace import Worktree  # noqa: E402
from tests.test_model import complete_sweep  # noqa: E402


def contract(action="proof"):
    return {
        "id": "ACC-100",
        "title": "Prove report parity",
        "action": action,
        "target_repo": "Mitch-be" if action == "code" else None,
        "domain": "api_ui_and_export_parity",
        "workspace_names": ["FusionTek (ws129)"],
        "root_cause_hypothesis": "The served surface may not share one source.",
        "acceptance_assertions": ["All compared surfaces match exactly."],
        "verification_plan": ["Collect fresh source and served values."],
        "moves_customer_numbers": False,
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


def judge_result(verdict="ACCEPT", full_sweep=None):
    result = {
        "verdict": verdict,
        "score": 0.96 if verdict == "ACCEPT" else 0.5,
        "summary": "Independent fixture verdict.",
        "hard_gates": {
            "contract_met": verdict == "ACCEPT",
            "regression_evidence": verdict == "ACCEPT",
            "source_reconciled": verdict == "ACCEPT",
            "freshness": verdict == "ACCEPT",
            "safety": True,
        },
        "findings": [] if verdict == "ACCEPT" else ["Evidence is incomplete."],
        "rework_instructions": [] if verdict == "ACCEPT" else ["Collect the missing evidence."],
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
        self.assertFalse(os.path.exists(supervisor.contract_path + ".tmp"))

    def test_accepted_work_starts_next_spec_without_schedule_sleep(self):
        supervisor, runner = self.supervisor(
            [spec_result("proof"), build_result(), judge_result("ACCEPT"), spec_result("proof")]
        )

        supervisor.step()
        supervisor.step()
        supervisor.step()
        supervisor.step()

        self.assertEqual(runner.phases, ["spec", "build", "judge", "spec"])
        self.assertEqual(load_state(supervisor.state_path)["phase"], "build")

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

    def test_judge_cannot_accept_code_that_has_no_pr_handoff(self):
        supervisor, runner = self.supervisor(
            [spec_result("code"), build_result(), judge_result("ACCEPT")]
        )

        supervisor.step()
        supervisor.step()
        supervisor.step()

        self.assertEqual(runner.phases, ["spec", "build", "judge"])
        self.assertEqual(load_state(supervisor.state_path)["phase"], "rework")

    def test_final_state_is_persisted_before_delivered_worktree_cleanup(self):
        observed_states = []
        runner = ScriptedRunner(
            [spec_result("code"), delivered_code_result(), judge_result("ACCEPT")]
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

    def test_restart_resumes_recorded_judge_phase(self):
        supervisor, runner = self.supervisor([judge_result("BLOCKED")])
        supervisor.ensure_runtime()
        state = new_state()
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

    def test_two_accepted_full_sweeps_exit_proof_complete(self):
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        supervisor, _ = self.supervisor(
            [
                spec_result("proof"), build_result(first), judge_result("ACCEPT", first),
                spec_result("proof"), build_result(second), judge_result("ACCEPT", second),
            ]
        )

        for _ in range(6):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["clean_sweeps"]), 2)

    def test_full_sweep_without_matching_receipts_cannot_complete(self):
        sweep = complete_sweep("sweep-1")
        build = build_result(sweep)
        build["receipts"] = [{
            "kind": "verification_run", "id": "not-the-proof", "url": None,
            "status": "complete",
        }]
        supervisor, _ = self.supervisor([
            spec_result("proof"), build, judge_result("ACCEPT", sweep),
        ])

        for _ in range(3):
            supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(
            state["last_sweep_errors"],
            ["full sweep lacked matching build receipts and judge reproduction"],
        )

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
        state = new_state()
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
        state = new_state()
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
        verdict = judge_result("ACCEPT")
        verdict["resolved_blocker_ids"] = ["ACC-OLD"]
        supervisor, _ = self.supervisor([spec_result("proof"), build_result(), verdict])
        supervisor.ensure_runtime()
        state = load_state(supervisor.state_path)
        state["blockers"] = [
            {"id": "ACC-OLD", "summary": "Old", "owner": "Ops", "evidence_needed": ["sync"]}
        ]
        save_state(supervisor.state_path, state)

        for _ in range(3):
            supervisor.step()

        self.assertEqual(load_state(supervisor.state_path)["blockers"], [])

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

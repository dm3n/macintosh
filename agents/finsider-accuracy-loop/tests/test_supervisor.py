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
        "moves_customer_numbers": False,
        "wait_seconds": 0,
    }
    if full_sweep is not None:
        result["full_sweep"] = full_sweep
    return result


def complete_sweep(sweep_id):
    return {
        "sweep_id": sweep_id,
        "observed_at": "2026-08-06T22:00:00Z",
        "data_watermark": "2026-08-06T21:30:00Z",
        "latest_sync_watermark": "2026-08-06T21:00:00Z",
        "latest_deploy_watermark": "2026-08-06T20:00:00Z",
        "active_workspaces": 30,
        "verified_workspaces": 30,
        "mismatches": 0,
        "errors": 0,
        "unknowns": 0,
        "stale": 0,
        "unresolved_surfaces": 0,
        "onboarding_gate_verified": True,
        "domains": {
            domain: {"status": "proved", "evidence": ["evidence:%s" % domain]}
            for domain in REQUIRED_DOMAINS
        },
    }


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
        "wait_seconds": 0,
    }
    if full_sweep is not None:
        result["full_sweep"] = full_sweep
    return result


class ScriptedRunner:
    def __init__(self, results):
        self.results = list(results)
        self.phases = []
        self.prompts = []
        self.active_process = None

    def run(self, phase, prompt, schema, cwd):
        self.phases.append(phase)
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
        second = complete_sweep("sweep-2")
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

    def test_agent_failure_keeps_same_phase_and_sets_retry(self):
        supervisor, runner = self.supervisor([AgentFailure("rate limit", transient=True)])

        outcome = supervisor.step()

        state = load_state(supervisor.state_path)
        self.assertEqual(outcome, "retry")
        self.assertEqual(runner.phases, ["spec"])
        self.assertEqual(state["phase"], "spec")
        self.assertEqual(state["phase_attempts"], 1)
        self.assertIsNotNone(state["retry_at"])


if __name__ == "__main__":
    unittest.main()

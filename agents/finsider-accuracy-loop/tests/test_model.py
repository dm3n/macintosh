import json
import os
import sys
import tempfile
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.model import (  # noqa: E402
    REQUIRED_DOMAINS,
    advance_phase,
    load_state,
    new_state,
    record_accepted_sweep,
    save_state,
    validate_sweep,
)


def complete_sweep(sweep_id):
    return {
        "sweep_id": sweep_id,
        "judge_verdict": "ACCEPT",
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


class StateModelTests(unittest.TestCase):
    def test_new_state_starts_at_spec_with_every_domain_unknown(self):
        state = new_state()

        self.assertEqual(state["phase"], "spec")
        self.assertEqual(state["status"], "running")
        self.assertEqual(set(state["coverage"]), set(REQUIRED_DOMAINS))
        self.assertTrue(all(item["status"] == "unknown" for item in state["coverage"].values()))

    def test_state_round_trips_through_atomic_json_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "STATE.json")
            state = advance_phase(new_state(), "build")

            save_state(path, state)

            self.assertEqual(load_state(path), state)
            self.assertFalse(os.path.exists(path + ".tmp"))
            with open(path) as state_file:
                json.load(state_file)

    def test_two_distinct_complete_sweeps_finish(self):
        state = new_state()

        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))
        self.assertTrue(record_accepted_sweep(state, complete_sweep("sweep-2")))

        self.assertEqual(state["status"], "complete")
        self.assertEqual([item["sweep_id"] for item in state["clean_sweeps"]], ["sweep-1", "sweep-2"])

    def test_same_sweep_cannot_count_twice(self):
        state = new_state()

        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))
        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))

        self.assertEqual(len(state["clean_sweeps"]), 1)

    def test_dirty_sweep_resets_consecutive_clean_evidence(self):
        state = new_state()
        record_accepted_sweep(state, complete_sweep("sweep-1"))
        dirty = complete_sweep("sweep-2")
        dirty["mismatches"] = 1

        self.assertFalse(record_accepted_sweep(state, dirty))

        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(state["status"], "running")

    def test_missing_or_unproved_domain_never_finishes(self):
        missing = complete_sweep("sweep-1")
        missing["domains"].pop(REQUIRED_DOMAINS[0])
        unproved = complete_sweep("sweep-2")
        unproved["domains"][REQUIRED_DOMAINS[0]] = {"status": "unknown", "evidence": []}

        self.assertIn("domain set is incomplete", validate_sweep(missing))
        self.assertTrue(any("is not proved" in error for error in validate_sweep(unproved)))

    def test_rejects_unfresh_or_unjudged_sweep(self):
        stale = complete_sweep("sweep-1")
        stale["observed_at"] = "2026-08-06T19:00:00Z"
        rejected = complete_sweep("sweep-2")
        rejected["judge_verdict"] = "REJECT"

        self.assertTrue(any("older than" in error for error in validate_sweep(stale)))
        self.assertIn("judge did not accept the sweep", validate_sweep(rejected))

    def test_rejects_unknowns_staleness_and_workspace_coverage_gaps(self):
        sweep = complete_sweep("sweep-1")
        sweep["unknowns"] = 1
        sweep["stale"] = 1
        sweep["verified_workspaces"] = 29
        sweep["onboarding_gate_verified"] = False

        errors = validate_sweep(sweep)

        self.assertTrue(any("unknowns must be zero" in error for error in errors))
        self.assertTrue(any("stale must be zero" in error for error in errors))
        self.assertTrue(any("workspace coverage" in error for error in errors))
        self.assertIn("onboarding accuracy gate is not verified", errors)


if __name__ == "__main__":
    unittest.main()

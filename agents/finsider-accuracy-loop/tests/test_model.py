import json
import os
import sys
import tempfile
import unittest


PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE_ROOT)

from accuracy_loop.model import (  # noqa: E402
    REQUIRED_DIMENSIONS,
    REQUIRED_DOMAINS,
    REQUIRED_LAYERS,
    REQUIRED_SURFACES,
    _workspace_roster_checksum,
    advance_phase,
    load_state,
    new_state,
    record_accepted_sweep,
    save_state,
    validate_sweep,
)


def evidence(evidence_id, observed_at="2026-08-06T22:00:00Z"):
    return {
        "kind": "verification_run",
        "id": evidence_id,
        "source": "finsider-verification",
        "observed_at": observed_at,
        "workspace_ids": ["ws129", "ws130"],
        "periods": ["all_supported_history"],
        "layers": list(REQUIRED_LAYERS),
        "dimensions": list(REQUIRED_DIMENSIONS),
        "surfaces": list(REQUIRED_SURFACES),
    }


def refresh_roster_snapshot(sweep):
    authoritative = sweep["authoritative_roster"]
    checksum = _workspace_roster_checksum(sweep["workspace_roster"])
    authoritative["checksum"] = checksum
    authoritative["workspace_ids"] = [
        item["workspace_id"] for item in sweep["workspace_roster"]
    ]
    authoritative["id"] = "roster:%s:%s" % (checksum, authoritative["observed_at"])


def complete_sweep(sweep_id, observed_at="2026-08-06T22:00:00Z"):
    verification_suffix = sweep_id.rsplit("-", 1)[-1]
    proof = evidence("evidence:%s" % sweep_id, observed_at)
    sweep = {
        "sweep_id": sweep_id,
        "judge_verdict": "ACCEPT",
        "observed_at": observed_at,
        "data_watermark": "2026-08-06T21:30:00Z",
        "latest_sync_watermark": "2026-08-06T21:00:00Z",
        "latest_deploy_watermark": "2026-08-06T20:00:00Z",
        "active_workspaces": 2,
        "verified_workspaces": 2,
        "mismatches": 0,
        "errors": 0,
        "unknowns": 0,
        "stale": 0,
        "unresolved_surfaces": 0,
        "onboarding_gate_verified": True,
        "authoritative_roster": {
            "kind": "authoritative_workspace_roster",
            "id": "pending",
            "source": "finsider-verification:list_workspaces",
            "observed_at": observed_at,
            "workspace_ids": ["ws129", "ws130", "ws999"],
            "checksum": "pending",
        },
        "workspace_roster": [
            {
                "workspace_id": "ws129",
                "name": "FusionTek",
                "lifecycle": "active",
                "included": True,
                "latest_sync_at": "2026-08-06T21:00:00Z",
                "verification_id": "verify-ws129-%s" % verification_suffix,
                "verified_at": observed_at,
            },
            {
                "workspace_id": "ws130",
                "name": "Acme",
                "lifecycle": "active",
                "included": True,
                "latest_sync_at": "2026-08-06T21:05:00Z",
                "verification_id": "verify-ws130-%s" % verification_suffix,
                "verified_at": observed_at,
            },
            {
                "workspace_id": "ws999",
                "name": "Archived Fixture",
                "lifecycle": "archived",
                "included": False,
                "exclusion_reason": "Archived in the authoritative workspace roster.",
            },
        ],
        "domains": {
            domain: {"status": "proved", "evidence": [proof]}
            for domain in REQUIRED_DOMAINS
        },
        "scope": {
            "periods": {
                "coverage": "all_supported_history",
                "evidence": [proof],
            },
            "layers": {
                "required": list(REQUIRED_LAYERS),
                "covered": list(REQUIRED_LAYERS),
                "evidence": [proof],
            },
            "dimensions": {
                "required": list(REQUIRED_DIMENSIONS),
                "covered": list(REQUIRED_DIMENSIONS),
                "evidence": [proof],
            },
            "surfaces": {
                surface: {"status": "proved", "evidence": [proof]}
                for surface in REQUIRED_SURFACES
            },
        },
    }
    refresh_roster_snapshot(sweep)
    return sweep


class StateModelTests(unittest.TestCase):
    def test_new_state_starts_at_spec_with_every_domain_unknown(self):
        state = new_state()

        self.assertEqual(state["phase"], "spec")
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["delivery_candidates"], [])
        self.assertEqual(state["completed_operation_ids"], [])
        self.assertEqual(state["historical_completed_contract_ids"], [])
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

    def test_v1_state_migration_assigns_stable_blocker_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "STATE.json")
            legacy = new_state()
            legacy["schema_version"] = 1
            legacy.pop("action_intent")
            legacy.pop("contract_sha256")
            legacy["blockers"] = [{
                "contract_id": "ACC-LEGACY",
                "summary": "Old blocker",
                "findings": ["Need a fresh sync."],
            }]
            with open(path, "w") as state_file:
                json.dump(legacy, state_file)

            migrated = load_state(path)

            self.assertEqual(migrated["schema_version"], 2)
            self.assertEqual(migrated["blockers"][0]["id"], "ACC-LEGACY")
            self.assertEqual(migrated["blockers"][0]["evidence_needed"], ["Need a fresh sync."])

    def test_existing_v2_state_defaults_convergence_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "STATE.json")
            existing = new_state()
            existing.pop("completed_contract_ids", None)
            existing.pop("delivery_candidates", None)
            existing.pop("completed_operation_ids", None)
            existing.pop("historical_completed_contract_ids", None)
            with open(path, "w") as state_file:
                json.dump(existing, state_file)

            loaded = load_state(path)

            self.assertEqual(loaded["completed_contract_ids"], [])
            self.assertEqual(loaded["delivery_candidates"], [])
            self.assertEqual(loaded["completed_operation_ids"], [])
            self.assertEqual(loaded["historical_completed_contract_ids"], [])

    def test_two_distinct_complete_sweeps_finish(self):
        state = new_state()
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")

        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))
        self.assertTrue(record_accepted_sweep(state, second))

        self.assertEqual(state["status"], "certified")
        self.assertEqual([item["sweep_id"] for item in state["clean_sweeps"]], ["sweep-1", "sweep-2"])

    def test_same_sweep_cannot_count_twice(self):
        state = new_state()

        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))
        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))

        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(state["last_sweep_errors"], ["sweep_id was replayed"])

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
        sweep["verified_workspaces"] = 1
        sweep["onboarding_gate_verified"] = False

        errors = validate_sweep(sweep)

        self.assertTrue(any("unknowns must be integer zero" in error for error in errors))
        self.assertTrue(any("stale must be integer zero" in error for error in errors))
        self.assertTrue(any("workspace coverage" in error for error in errors))
        self.assertIn("onboarding accuracy gate is not verified", errors)

    def test_rejects_boolean_or_float_counts_and_empty_evidence_values(self):
        sweep = complete_sweep("sweep-1")
        sweep["mismatches"] = False
        sweep["verified_workspaces"] = 2.0
        sweep["domains"][REQUIRED_DOMAINS[0]]["evidence"] = [""]

        errors = validate_sweep(sweep)

        self.assertTrue(any("verified_workspaces must be an integer" in error for error in errors))
        self.assertTrue(any("mismatches must be integer zero" in error for error in errors))
        self.assertTrue(any("not structured evidence" in error for error in errors))

    def test_rejects_timestamp_without_timezone(self):
        sweep = complete_sweep("sweep-1")
        sweep["observed_at"] = "2026-08-06T22:00:00"

        self.assertTrue(any("timezone" in error for error in validate_sweep(sweep)))

    def test_second_sweep_must_be_observed_later_than_first(self):
        state = new_state()
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2")

        self.assertFalse(record_accepted_sweep(state, first))
        self.assertFalse(record_accepted_sweep(state, second))

        self.assertEqual(state["status"], "running")
        self.assertEqual(state["last_sweep_errors"], ["clean sweep observation did not advance"])
        self.assertEqual(state["clean_sweeps"], [])

    def test_unresolved_blocker_prevents_completion_candidate(self):
        state = new_state()
        state["blockers"] = [{"id": "ACC-BLOCKED", "summary": "Source auth is stale."}]

        self.assertFalse(record_accepted_sweep(state, complete_sweep("sweep-1")))

        self.assertEqual(state["clean_sweeps"], [])
        self.assertIn("unresolved blockers remain", state["last_sweep_errors"])

    def test_rejects_missing_roster_scope_or_surface_proof(self):
        missing_roster = complete_sweep("sweep-1")
        missing_roster.pop("workspace_roster")
        missing_scope = complete_sweep("sweep-2")
        missing_scope.pop("scope")
        missing_surface = complete_sweep("sweep-3")
        missing_surface["scope"]["surfaces"].pop(REQUIRED_SURFACES[0])

        self.assertIn("workspace_roster is missing", validate_sweep(missing_roster))
        self.assertIn("scope is missing", validate_sweep(missing_scope))
        self.assertIn("surface set is incomplete", validate_sweep(missing_surface))

    def test_roster_must_match_authoritative_inventory_identity(self):
        sweep = complete_sweep("sweep-1")
        sweep["authoritative_roster"]["workspace_ids"] = ["ws129", "ws999"]

        self.assertIn(
            "workspace_roster does not match the authoritative roster", validate_sweep(sweep)
        )

    def test_authoritative_roster_is_fresh_and_content_bound(self):
        stale = complete_sweep("sweep-stale")
        stale["authoritative_roster"]["observed_at"] = "2026-08-06T20:00:00Z"
        refresh_roster_snapshot(stale)
        tampered = complete_sweep("sweep-tampered")
        tampered["workspace_roster"][0]["name"] = "Changed without a new snapshot"

        self.assertIn(
            "authoritative roster predates a required watermark", validate_sweep(stale)
        )
        self.assertIn(
            "authoritative roster checksum does not match the roster", validate_sweep(tampered)
        )

    def test_domain_evidence_must_cover_every_active_workspace(self):
        sweep = complete_sweep("sweep-1")
        sweep["domains"][REQUIRED_DOMAINS[0]]["evidence"][0]["workspace_ids"] = ["ws129"]

        errors = validate_sweep(sweep)

        self.assertIn(
            "domain %s does not cover every active workspace" % REQUIRED_DOMAINS[0], errors
        )

    def test_evidence_must_be_fresh_for_each_workspace_and_canonically_scoped(self):
        stale = complete_sweep("sweep-1")
        stale["domains"][REQUIRED_DOMAINS[0]]["evidence"][0][
            "observed_at"
        ] = "2026-08-06T20:00:00Z"
        invalid_scope = complete_sweep("sweep-2")
        invalid_scope["domains"][REQUIRED_DOMAINS[0]]["evidence"][0]["layers"] = [
            "invented"
        ]

        stale_errors = validate_sweep(stale)
        scope_errors = validate_sweep(invalid_scope)

        self.assertTrue(any("predates workspace" in error for error in stale_errors))
        self.assertTrue(any("layer scope is not canonical" in error for error in scope_errors))

    def test_future_sweep_or_evidence_is_rejected(self):
        sweep = complete_sweep("sweep-future", "2099-08-06T22:00:00Z")

        errors = validate_sweep(sweep)

        self.assertIn("observed_at cannot be in the future", errors)
        self.assertTrue(any("future observation" in error for error in errors))

    def test_second_sweep_requires_new_per_workspace_verification_ids(self):
        state = new_state()
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        second["workspace_roster"][0]["verification_id"] = first[
            "workspace_roster"
        ][0]["verification_id"]

        self.assertFalse(record_accepted_sweep(state, first))
        self.assertFalse(record_accepted_sweep(state, second))

        self.assertEqual(state["clean_sweeps"], [])
        self.assertIn("reused its verification_id", state["last_sweep_errors"][0])

    def test_second_sweep_requires_a_new_authoritative_roster_snapshot(self):
        state = new_state()
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        second["authoritative_roster"]["id"] = first["authoritative_roster"]["id"]
        second["authoritative_roster"]["observed_at"] = first[
            "authoritative_roster"
        ]["observed_at"]

        self.assertFalse(record_accepted_sweep(state, first))
        self.assertFalse(record_accepted_sweep(state, second))

        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(
            state["last_sweep_errors"], ["authoritative roster snapshot was replayed"]
        )

    def test_second_sweep_cannot_reuse_domain_or_surface_evidence(self):
        state = new_state()
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        reused_id = first["domains"][REQUIRED_DOMAINS[0]]["evidence"][0]["id"]
        second["domains"][REQUIRED_DOMAINS[0]]["evidence"][0]["id"] = reused_id

        self.assertFalse(record_accepted_sweep(state, first))
        self.assertFalse(record_accepted_sweep(state, second))

        self.assertEqual(state["clean_sweeps"], [])
        self.assertEqual(
            state["last_sweep_errors"], ["proof evidence was replayed between clean sweeps"]
        )

    def test_roster_change_restarts_consecutive_proof_sequence(self):
        state = new_state()
        first = complete_sweep("sweep-1")
        second = complete_sweep("sweep-2", "2026-08-06T22:05:00Z")
        second["workspace_roster"].append({
            "workspace_id": "ws1000",
            "name": "Test Fixture",
            "lifecycle": "test",
            "included": False,
            "exclusion_reason": "Marked test in the authoritative roster.",
        })
        second["authoritative_roster"]["workspace_ids"].append("ws1000")
        refresh_roster_snapshot(second)

        self.assertFalse(record_accepted_sweep(state, first))
        self.assertFalse(record_accepted_sweep(state, second))

        self.assertEqual([item["sweep_id"] for item in state["clean_sweeps"]], ["sweep-2"])
        self.assertIn("roster changed", state["last_sweep_errors"][0])


if __name__ == "__main__":
    unittest.main()

"""Durable state and deterministic proof-completion rules."""

import copy
import json
import os
from datetime import datetime, timezone


SCHEMA_VERSION = 1
PHASES = ("spec", "build", "judge", "rework")

REQUIRED_DOMAINS = (
    "source_connections_and_sync_freshness",
    "tenant_and_workspace_scoping",
    "chart_of_accounts_and_classification",
    "report_snapshot_integrity",
    "profit_and_loss",
    "balance_sheet",
    "cash_flow",
    "adjustments_and_bridge_layers",
    "cash_proof_and_bank_reconciliation",
    "kpis_and_derived_metrics",
    "flux_and_period_comparisons",
    "quality_of_earnings_reports",
    "transaction_drilldowns",
    "dashboards_and_board_reporting",
    "excel_and_workbook_exports",
    "ai_cfo_and_agent_numeric_outputs",
    "deal_and_forecast_models",
    "api_ui_and_export_parity",
    "onboarding_accuracy_gate",
    "rounding_period_key_and_dimension_behavior",
)

REQUIRED_SURFACES = (
    "source_api",
    "report_api",
    "profit_and_loss_ui",
    "balance_sheet_ui",
    "cash_flow_ui",
    "adjustments_ui",
    "cash_proof_ui",
    "kpi_ui",
    "flux_ui",
    "quality_of_earnings_ui",
    "transaction_drilldowns_ui",
    "dashboard_ui",
    "board_reporting_ui",
    "excel_export",
    "ai_cfo",
    "finsider_mcp",
    "deal_model",
    "forecast_model",
    "onboarding",
)

REQUIRED_LAYERS = ("original", "adjusted", "bridge")
REQUIRED_DIMENSIONS = ("workspace", "tracking_category")
LIFECYCLE_STATES = ("active", "archived", "test", "unsupported")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_state():
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "running",
        "phase": "spec",
        "cycle": 0,
        "phase_attempts": 0,
        "retry_at": None,
        "active_contract": None,
        "spec_result": None,
        "build_result": None,
        "judge_result": None,
        "action_intent": None,
        "worktree": None,
        "rework_count": 0,
        "coverage": {
            domain: {"status": "unknown", "evidence": []}
            for domain in REQUIRED_DOMAINS
        },
        "blockers": [],
        "clean_sweeps": [],
        "last_error": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def load_state(path):
    with open(path) as state_file:
        state = json.load(state_file)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported state schema version")
    return state


def save_state(path, state):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    state["updated_at"] = utc_now()
    temporary_path = path + ".tmp"
    with open(temporary_path, "w") as state_file:
        json.dump(state, state_file, indent=2, sort_keys=True)
        state_file.write("\n")
        state_file.flush()
        os.fsync(state_file.fileno())
    os.replace(temporary_path, path)


def advance_phase(state, phase):
    if phase not in PHASES:
        raise ValueError("unknown phase: %s" % phase)
    updated = copy.deepcopy(state)
    updated["phase"] = phase
    updated["phase_attempts"] = 0
    updated["retry_at"] = None
    updated["last_error"] = None
    updated["updated_at"] = utc_now()
    return updated


def _parse_timestamp(value, field, errors):
    if not isinstance(value, str) or not value:
        errors.append("%s is missing" % field)
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append("%s is not an ISO-8601 timestamp" % field)
        return None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        errors.append("%s must include a timezone" % field)
        return None
    return timestamp


def _valid_nonempty_strings(value):
    return (
        isinstance(value, list)
        and value
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _validate_evidence(evidence, field, errors):
    if not isinstance(evidence, list) or not evidence:
        errors.append("%s has no structured evidence" % field)
        return set()
    covered_workspaces = set()
    required_fields = (
        "kind", "id", "source", "observed_at", "workspace_ids", "periods",
        "layers", "dimensions", "surfaces",
    )
    for index, item in enumerate(evidence):
        item_field = "%s[%s]" % (field, index)
        if not isinstance(item, dict):
            errors.append("%s is not structured evidence" % item_field)
            continue
        for key in required_fields[:3]:
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append("%s.%s is missing" % (item_field, key))
        _parse_timestamp(item.get("observed_at"), "%s.observed_at" % item_field, errors)
        for key in required_fields[4:]:
            if not _valid_nonempty_strings(item.get(key)):
                errors.append("%s.%s must be non-empty strings" % (item_field, key))
        if _valid_nonempty_strings(item.get("workspace_ids")):
            covered_workspaces.update(item["workspace_ids"])
    return covered_workspaces


def _validate_workspace_roster(sweep, deploy_watermark, errors):
    roster = sweep.get("workspace_roster")
    if not isinstance(roster, list) or not roster:
        errors.append("workspace_roster is missing")
        return set(), {}

    seen = set()
    active_ids = set()
    active_by_id = {}
    for index, workspace in enumerate(roster):
        field = "workspace_roster[%s]" % index
        if not isinstance(workspace, dict):
            errors.append("%s is not an object" % field)
            continue
        workspace_id = workspace.get("workspace_id")
        name = workspace.get("name")
        lifecycle = workspace.get("lifecycle")
        included = workspace.get("included")
        if not isinstance(workspace_id, str) or not workspace_id.strip():
            errors.append("%s.workspace_id is missing" % field)
            continue
        if workspace_id in seen:
            errors.append("workspace_roster has duplicate workspace_id %s" % workspace_id)
        seen.add(workspace_id)
        if not isinstance(name, str) or not name.strip():
            errors.append("%s.name is missing" % field)
        if lifecycle not in LIFECYCLE_STATES:
            errors.append("%s.lifecycle is invalid" % field)
            continue
        if type(included) is not bool:
            errors.append("%s.included must be boolean" % field)
            continue
        if lifecycle == "active":
            if included is not True:
                errors.append("active workspace %s is excluded" % workspace_id)
            active_ids.add(workspace_id)
            active_by_id[workspace_id] = workspace
            sync_at = _parse_timestamp(
                workspace.get("latest_sync_at"), "%s.latest_sync_at" % field, errors
            )
            verified_at = _parse_timestamp(
                workspace.get("verified_at"), "%s.verified_at" % field, errors
            )
            verification_id = workspace.get("verification_id")
            if not isinstance(verification_id, str) or not verification_id.strip():
                errors.append("%s.verification_id is missing" % field)
            if verified_at and sync_at and verified_at < sync_at:
                errors.append("workspace %s was verified before its latest sync" % workspace_id)
            if verified_at and deploy_watermark and verified_at < deploy_watermark:
                errors.append("workspace %s was verified before the latest deploy" % workspace_id)
        else:
            if included is not False:
                errors.append("inactive workspace %s cannot be included" % workspace_id)
            if not isinstance(workspace.get("exclusion_reason"), str) or not workspace[
                "exclusion_reason"
            ].strip():
                errors.append("inactive workspace %s has no exclusion reason" % workspace_id)
    return active_ids, active_by_id


def _validate_scope(scope, active_ids, errors):
    if not isinstance(scope, dict):
        errors.append("scope is missing")
        return

    periods = scope.get("periods", {})
    if periods.get("coverage") != "all_supported_history":
        errors.append("period scope is not all_supported_history")
    if _validate_evidence(periods.get("evidence"), "scope.periods.evidence", errors) != active_ids:
        errors.append("period evidence does not cover every active workspace")

    for key, required in (("layers", REQUIRED_LAYERS), ("dimensions", REQUIRED_DIMENSIONS)):
        section = scope.get(key, {})
        if section.get("required") != list(required):
            errors.append("%s required set is not canonical" % key)
        covered = section.get("covered")
        if not isinstance(covered, list) or set(covered) != set(required):
            errors.append("%s coverage is incomplete" % key)
        if _validate_evidence(section.get("evidence"), "scope.%s.evidence" % key, errors) != active_ids:
            errors.append("%s evidence does not cover every active workspace" % key)

    surfaces = scope.get("surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(REQUIRED_SURFACES):
        errors.append("surface set is incomplete")
        return
    for surface in REQUIRED_SURFACES:
        proof = surfaces.get(surface, {})
        if proof.get("status") != "proved":
            errors.append("surface %s is not proved" % surface)
        covered = _validate_evidence(
            proof.get("evidence"), "scope.surfaces.%s.evidence" % surface, errors
        )
        if covered != active_ids:
            errors.append("surface %s does not cover every active workspace" % surface)


def validate_sweep(sweep):
    errors = []
    if sweep.get("judge_verdict") != "ACCEPT":
        errors.append("judge did not accept the sweep")
    if not sweep.get("sweep_id"):
        errors.append("sweep_id is missing")

    active = sweep.get("active_workspaces")
    verified = sweep.get("verified_workspaces")
    if type(active) is not int or active <= 0:
        errors.append("active_workspaces must be a positive integer")
    if type(verified) is not int:
        errors.append("verified_workspaces must be an integer")
    if type(active) is int and type(verified) is int and active != verified:
        errors.append("workspace coverage is incomplete")

    for field in ("mismatches", "errors", "unknowns", "stale", "unresolved_surfaces"):
        if type(sweep.get(field)) is not int or sweep.get(field) != 0:
            errors.append("%s must be integer zero" % field)

    if sweep.get("onboarding_gate_verified") is not True:
        errors.append("onboarding accuracy gate is not verified")

    observed_at = _parse_timestamp(sweep.get("observed_at"), "observed_at", errors)
    data_watermark = _parse_timestamp(sweep.get("data_watermark"), "data_watermark", errors)
    sync_watermark = _parse_timestamp(
        sweep.get("latest_sync_watermark"), "latest_sync_watermark", errors
    )
    deploy_watermark = _parse_timestamp(
        sweep.get("latest_deploy_watermark"), "latest_deploy_watermark", errors
    )
    active_ids, _active_by_id = _validate_workspace_roster(sweep, deploy_watermark, errors)
    if type(active) is int and len(active_ids) != active:
        errors.append("active_workspaces does not match the workspace roster")
    if type(verified) is int and len(active_ids) != verified:
        errors.append("verified_workspaces does not match the workspace roster")

    domains = sweep.get("domains")
    if not isinstance(domains, dict) or set(domains) != set(REQUIRED_DOMAINS):
        errors.append("domain set is incomplete")
    if isinstance(domains, dict):
        for domain in REQUIRED_DOMAINS:
            proof = domains.get(domain, {})
            if proof.get("status") != "proved":
                errors.append("domain %s is not proved" % domain)
            covered = _validate_evidence(
                proof.get("evidence"), "domains.%s.evidence" % domain, errors
            )
            if covered != active_ids:
                errors.append("domain %s does not cover every active workspace" % domain)

    _validate_scope(sweep.get("scope"), active_ids, errors)
    freshness_inputs = [item for item in (data_watermark, sync_watermark, deploy_watermark) if item]
    if observed_at and freshness_inputs and observed_at < max(freshness_inputs):
        errors.append("observed_at is older than a required watermark")
    if data_watermark and sync_watermark and data_watermark < sync_watermark:
        errors.append("data_watermark is older than the latest sync watermark")

    return errors


def record_accepted_sweep(state, sweep):
    errors = validate_sweep(sweep)
    if state.get("blockers"):
        errors.append("unresolved blockers remain")
    state["last_sweep_errors"] = errors
    state["status"] = "running"
    if errors:
        state["clean_sweeps"] = []
        return False

    existing_ids = {item["sweep_id"] for item in state.get("clean_sweeps", [])}
    if sweep["sweep_id"] in existing_ids:
        state["clean_sweeps"] = []
        state["last_sweep_errors"] = ["sweep_id was replayed"]
        return False

    clean_sweeps = list(state.get("clean_sweeps", []))
    if clean_sweeps:
        previous = clean_sweeps[-1]
        for field in ("data_watermark", "latest_sync_watermark", "latest_deploy_watermark"):
            previous_watermark = _parse_timestamp(previous.get(field), field, [])
            current_watermark = _parse_timestamp(sweep.get(field), field, [])
            if previous_watermark and current_watermark and current_watermark < previous_watermark:
                state["clean_sweeps"] = []
                state["last_sweep_errors"] = ["%s regressed between clean sweeps" % field]
                return False
        previous_observed = _parse_timestamp(previous.get("observed_at"), "observed_at", [])
        current_observed = _parse_timestamp(sweep.get("observed_at"), "observed_at", [])
        if previous_observed and current_observed and current_observed <= previous_observed:
            state["clean_sweeps"] = []
            state["last_sweep_errors"] = ["clean sweep observation did not advance"]
            return False

        previous_roster = {
            (item["workspace_id"], item["lifecycle"], item["included"])
            for item in previous["workspace_roster"]
        }
        current_roster = {
            (item["workspace_id"], item["lifecycle"], item["included"])
            for item in sweep["workspace_roster"]
        }
        if current_roster != previous_roster:
            state["clean_sweeps"] = [copy.deepcopy(sweep)]
            state["last_sweep_errors"] = ["workspace roster changed; proof sequence restarted"]
            return False
        previous_active = {
            item["workspace_id"]: item
            for item in previous["workspace_roster"] if item["lifecycle"] == "active"
        }
        current_active = {
            item["workspace_id"]: item
            for item in sweep["workspace_roster"] if item["lifecycle"] == "active"
        }
        for workspace_id, current in current_active.items():
            old = previous_active[workspace_id]
            if current["verification_id"] == old["verification_id"]:
                state["clean_sweeps"] = []
                state["last_sweep_errors"] = [
                    "workspace %s reused its verification_id" % workspace_id
                ]
                return False
            old_verified = _parse_timestamp(old.get("verified_at"), "verified_at", [])
            new_verified = _parse_timestamp(current.get("verified_at"), "verified_at", [])
            if old_verified and new_verified and new_verified <= old_verified:
                state["clean_sweeps"] = []
                state["last_sweep_errors"] = [
                    "workspace %s verification did not advance" % workspace_id
                ]
                return False

    clean_sweeps.append(copy.deepcopy(sweep))
    state["clean_sweeps"] = clean_sweeps[-2:]
    if len(state["clean_sweeps"]) == 2:
        state["status"] = "complete"
        return True
    return False

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
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append("%s is not an ISO-8601 timestamp" % field)
        return None


def validate_sweep(sweep):
    errors = []
    if sweep.get("judge_verdict") != "ACCEPT":
        errors.append("judge did not accept the sweep")
    if not sweep.get("sweep_id"):
        errors.append("sweep_id is missing")

    active = sweep.get("active_workspaces")
    verified = sweep.get("verified_workspaces")
    if not isinstance(active, int) or active <= 0:
        errors.append("active_workspaces must be a positive integer")
    if active != verified:
        errors.append("workspace coverage is incomplete")

    for field in ("mismatches", "errors", "unknowns", "stale", "unresolved_surfaces"):
        if sweep.get(field) != 0:
            errors.append("%s must be zero" % field)

    if sweep.get("onboarding_gate_verified") is not True:
        errors.append("onboarding accuracy gate is not verified")

    domains = sweep.get("domains")
    if not isinstance(domains, dict) or set(domains) != set(REQUIRED_DOMAINS):
        errors.append("domain set is incomplete")
    if isinstance(domains, dict):
        for domain in REQUIRED_DOMAINS:
            proof = domains.get(domain, {})
            if proof.get("status") != "proved":
                errors.append("domain %s is not proved" % domain)
            evidence = proof.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.append("domain %s has no evidence" % domain)

    observed_at = _parse_timestamp(sweep.get("observed_at"), "observed_at", errors)
    data_watermark = _parse_timestamp(sweep.get("data_watermark"), "data_watermark", errors)
    sync_watermark = _parse_timestamp(
        sweep.get("latest_sync_watermark"), "latest_sync_watermark", errors
    )
    deploy_watermark = _parse_timestamp(
        sweep.get("latest_deploy_watermark"), "latest_deploy_watermark", errors
    )
    freshness_inputs = [item for item in (data_watermark, sync_watermark, deploy_watermark) if item]
    if observed_at and freshness_inputs and observed_at < max(freshness_inputs):
        errors.append("observed_at is older than a required watermark")
    if data_watermark and sync_watermark and data_watermark < sync_watermark:
        errors.append("data_watermark is older than the latest sync watermark")

    return errors


def record_accepted_sweep(state, sweep):
    errors = validate_sweep(sweep)
    state["last_sweep_errors"] = errors
    state["status"] = "running"
    if errors:
        state["clean_sweeps"] = []
        return False

    existing_ids = {item["sweep_id"] for item in state.get("clean_sweeps", [])}
    if sweep["sweep_id"] in existing_ids:
        return False

    clean_sweeps = list(state.get("clean_sweeps", []))
    if clean_sweeps:
        previous = clean_sweeps[-1]
        previous_watermark = _parse_timestamp(previous.get("data_watermark"), "data_watermark", [])
        current_watermark = _parse_timestamp(sweep.get("data_watermark"), "data_watermark", [])
        if previous_watermark and current_watermark and current_watermark < previous_watermark:
            state["clean_sweeps"] = []
            state["last_sweep_errors"] = ["data watermark regressed between clean sweeps"]
            return False

    clean_sweeps.append(copy.deepcopy(sweep))
    state["clean_sweeps"] = clean_sweeps[-2:]
    if len(state["clean_sweeps"]) == 2:
        state["status"] = "complete"
        return True
    return False

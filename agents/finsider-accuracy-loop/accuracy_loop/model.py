"""Durable state and deterministic proof-completion rules."""

import copy
import hashlib
import json
import os
from datetime import datetime, timezone


SCHEMA_VERSION = 2
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
        "completed_contract_ids": [],
        "completed_operation_ids": [],
        "historical_completed_contract_ids": [],
        "delivery_candidates": [],
        "quarantined_deliveries": [],
        "clean_sweeps": [],
        "contract_sha256": None,
        "last_error": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def load_state(path):
    with open(path) as state_file:
        state = json.load(state_file)
    if state.get("schema_version") == 1:
        state = _migrate_v1_state(state)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported state schema version")
    state.setdefault("completed_contract_ids", [])
    state.setdefault("completed_operation_ids", [])
    state.setdefault("historical_completed_contract_ids", [])
    state.setdefault("delivery_candidates", [])
    state.setdefault("quarantined_deliveries", [])
    return state


def _migrate_v1_state(state):
    migrated = copy.deepcopy(state)
    blockers = []
    for blocker in migrated.get("blockers", []):
        if not isinstance(blocker, dict):
            blocker = {"summary": str(blocker)}
        identity = blocker.get("id") or blocker.get("contract_id")
        if not identity:
            digest = hashlib.sha256(
                json.dumps(blocker, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:12]
            identity = "legacy:%s" % digest
        evidence_needed = blocker.get("evidence_needed")
        if not _valid_nonempty_strings(evidence_needed):
            evidence_needed = blocker.get("findings")
        if not _valid_nonempty_strings(evidence_needed):
            evidence_needed = ["Fresh direct evidence that resolves this blocker."]
        blocker.update({
            "id": identity,
            "summary": blocker.get("summary") or blocker.get("title") or identity,
            "owner": blocker.get("owner") or "Finsider accuracy loop",
            "evidence_needed": evidence_needed,
        })
        blockers.append(blocker)
    migrated["blockers"] = blockers
    migrated.setdefault("completed_contract_ids", [])
    migrated.setdefault("completed_operation_ids", [])
    migrated.setdefault("historical_completed_contract_ids", [])
    migrated.setdefault("delivery_candidates", [])
    migrated.setdefault("quarantined_deliveries", [])
    migrated.setdefault("action_intent", None)
    migrated.setdefault("contract_sha256", None)
    migrated["schema_version"] = SCHEMA_VERSION
    return migrated


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


def _validate_evidence(
    evidence,
    field,
    errors,
    active_by_id=None,
    deploy_watermark=None,
    sweep_observed=None,
):
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
        timestamp_errors = []
        evidence_time = _parse_timestamp(
            item.get("observed_at"), "%s.observed_at" % item_field, timestamp_errors
        )
        if evidence_time:
            if sweep_observed and evidence_time > sweep_observed:
                errors.append("%s was observed after the sweep" % item_field)
            if evidence_time > datetime.now(timezone.utc):
                errors.append("%s has a future observation" % item_field)
            if deploy_watermark and evidence_time < deploy_watermark:
                errors.append("%s predates the latest deploy" % item_field)
            for workspace_id in item.get("workspace_ids", []):
                workspace = (active_by_id or {}).get(workspace_id)
                if workspace is None:
                    errors.append("%s references a non-active workspace %s" % (
                        item_field, workspace_id
                    ))
                    continue
                sync_at = _parse_timestamp(workspace.get("latest_sync_at"), "latest_sync_at", [])
                if sync_at and evidence_time < sync_at:
                    errors.append("%s predates workspace %s latest sync" % (
                        item_field, workspace_id
                    ))
        if set(item.get("periods", [])) != {"all_supported_history"}:
            errors.append("%s period scope is not canonical" % item_field)
        layers = item.get("layers", [])
        if not layers or not set(layers).issubset(set(REQUIRED_LAYERS)):
            errors.append("%s layer scope is not canonical" % item_field)
        dimensions = item.get("dimensions", [])
        if not dimensions or not set(dimensions).issubset(set(REQUIRED_DIMENSIONS)):
            errors.append("%s dimension scope is not canonical" % item_field)
        surfaces = item.get("surfaces", [])
        if not surfaces or not set(surfaces).issubset(set(REQUIRED_SURFACES)):
            errors.append("%s surface scope is not canonical" % item_field)
    return covered_workspaces


def _workspace_roster_checksum(roster):
    canonical = []
    for workspace in roster:
        if not isinstance(workspace, dict):
            continue
        canonical.append({
            key: workspace.get(key)
            for key in (
                "workspace_id", "name", "lifecycle", "included", "latest_sync_at",
                "exclusion_reason",
            )
            if key in workspace
        })
    canonical.sort(key=lambda item: str(item.get("workspace_id")))
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_workspace_roster(
    sweep, required_watermark, sweep_observed, errors
):
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
            if verified_at and required_watermark and verified_at < required_watermark:
                errors.append("workspace %s was verified before a required watermark" % workspace_id)
            if verified_at and sweep_observed and verified_at > sweep_observed:
                errors.append("workspace %s was verified after the sweep" % workspace_id)
            if verified_at and verified_at > datetime.now(timezone.utc):
                errors.append("workspace %s verification is in the future" % workspace_id)
        else:
            if included is not False:
                errors.append("inactive workspace %s cannot be included" % workspace_id)
            if not isinstance(workspace.get("exclusion_reason"), str) or not workspace[
                "exclusion_reason"
            ].strip():
                errors.append("inactive workspace %s has no exclusion reason" % workspace_id)
    authoritative = sweep.get("authoritative_roster")
    if not isinstance(authoritative, dict):
        errors.append("authoritative_roster is missing")
    else:
        if authoritative.get("kind") != "authoritative_workspace_roster":
            errors.append("authoritative_roster.kind is invalid")
        if authoritative.get("source") != "finsider-verification:list_workspaces":
            errors.append("authoritative_roster.source is invalid")
        if not isinstance(authoritative.get("id"), str) or not authoritative["id"].strip():
            errors.append("authoritative_roster.id is missing")
        roster_observed = _parse_timestamp(
            authoritative.get("observed_at"), "authoritative_roster.observed_at", errors
        )
        if roster_observed and sweep_observed and roster_observed > sweep_observed:
            errors.append("authoritative roster was observed after the sweep")
        if roster_observed and roster_observed > datetime.now(timezone.utc):
            errors.append("authoritative roster observation is in the future")
        if roster_observed and required_watermark and roster_observed < required_watermark:
            errors.append("authoritative roster predates a required watermark")
        checksum = _workspace_roster_checksum(roster)
        if authoritative.get("checksum") != checksum:
            errors.append("authoritative roster checksum does not match the roster")
        expected_id = "roster:%s:%s" % (checksum, authoritative.get("observed_at"))
        if authoritative.get("id") != expected_id:
            errors.append("authoritative roster ID is not bound to its snapshot")
        roster_ids = authoritative.get("workspace_ids")
        if not isinstance(roster_ids, list) or set(roster_ids) != seen or len(roster_ids) != len(seen):
            errors.append("workspace_roster does not match the authoritative roster")
    return active_ids, active_by_id


def _validate_scope(
    scope, active_ids, active_by_id, deploy_watermark, sweep_observed, errors
):
    if not isinstance(scope, dict):
        errors.append("scope is missing")
        return

    periods = scope.get("periods", {})
    if periods.get("coverage") != "all_supported_history":
        errors.append("period scope is not all_supported_history")
    if _validate_evidence(
        periods.get("evidence"), "scope.periods.evidence", errors,
        active_by_id, deploy_watermark, sweep_observed,
    ) != active_ids:
        errors.append("period evidence does not cover every active workspace")

    for key, required in (("layers", REQUIRED_LAYERS), ("dimensions", REQUIRED_DIMENSIONS)):
        section = scope.get(key, {})
        if section.get("required") != list(required):
            errors.append("%s required set is not canonical" % key)
        covered = section.get("covered")
        if not isinstance(covered, list) or set(covered) != set(required):
            errors.append("%s coverage is incomplete" % key)
        evidence = section.get("evidence")
        if _validate_evidence(
            evidence, "scope.%s.evidence" % key, errors,
            active_by_id, deploy_watermark, sweep_observed,
        ) != active_ids:
            errors.append("%s evidence does not cover every active workspace" % key)
        if isinstance(evidence, list):
            covered_scope = set()
            for item in evidence:
                if isinstance(item, dict):
                    covered_scope.update(item.get(key, []))
            if covered_scope != set(required):
                errors.append("%s structured evidence scope is incomplete" % key)

    surfaces = scope.get("surfaces")
    if not isinstance(surfaces, dict) or set(surfaces) != set(REQUIRED_SURFACES):
        errors.append("surface set is incomplete")
        return
    for surface in REQUIRED_SURFACES:
        proof = surfaces.get(surface, {})
        if proof.get("status") != "proved":
            errors.append("surface %s is not proved" % surface)
        covered = _validate_evidence(
            proof.get("evidence"), "scope.surfaces.%s.evidence" % surface, errors,
            active_by_id, deploy_watermark, sweep_observed,
        )
        if covered != active_ids:
            errors.append("surface %s does not cover every active workspace" % surface)
        if isinstance(proof.get("evidence"), list) and not all(
            surface in item.get("surfaces", [])
            for item in proof["evidence"] if isinstance(item, dict)
        ):
            errors.append("surface %s evidence does not name the surface" % surface)


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
    required_watermarks = [
        item for item in (data_watermark, sync_watermark, deploy_watermark) if item
    ]
    required_watermark = max(required_watermarks) if required_watermarks else None
    active_ids, active_by_id = _validate_workspace_roster(
        sweep, required_watermark, observed_at, errors
    )
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
                proof.get("evidence"), "domains.%s.evidence" % domain, errors,
                active_by_id, deploy_watermark, observed_at,
            )
            if covered != active_ids:
                errors.append("domain %s does not cover every active workspace" % domain)

    _validate_scope(
        sweep.get("scope"), active_ids, active_by_id, deploy_watermark, observed_at, errors
    )
    freshness_inputs = [item for item in (data_watermark, sync_watermark, deploy_watermark) if item]
    if observed_at and freshness_inputs and observed_at < max(freshness_inputs):
        errors.append("observed_at is older than a required watermark")
    if observed_at and observed_at > datetime.now(timezone.utc):
        errors.append("observed_at cannot be in the future")
    if data_watermark and sync_watermark and data_watermark < sync_watermark:
        errors.append("data_watermark is older than the latest sync watermark")

    return errors


def _evidence_identities(sweep):
    identities = set()
    evidence_lists = []
    for proof in sweep.get("domains", {}).values():
        if isinstance(proof, dict):
            evidence_lists.append(proof.get("evidence", []))
    scope = sweep.get("scope", {})
    for key in ("periods", "layers", "dimensions"):
        section = scope.get(key, {})
        if isinstance(section, dict):
            evidence_lists.append(section.get("evidence", []))
    for proof in scope.get("surfaces", {}).values():
        if isinstance(proof, dict):
            evidence_lists.append(proof.get("evidence", []))
    for evidence in evidence_lists:
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if isinstance(item, dict):
                identities.add((item.get("kind"), item.get("source"), item.get("id")))
    return identities


def record_accepted_sweep(state, sweep):
    errors = validate_sweep(sweep)
    if state.get("blockers"):
        errors.append("unresolved blockers remain")
    if state.get("delivery_candidates"):
        errors.append("unresolved delivery candidates remain")
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
        if sweep.get("latest_deploy_watermark") != previous.get(
            "latest_deploy_watermark"
        ):
            state["clean_sweeps"] = [copy.deepcopy(sweep)]
            state["last_sweep_errors"] = [
                "deployment changed; proof sequence restarted"
            ]
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
        previous_roster_evidence = previous["authoritative_roster"]
        current_roster_evidence = sweep["authoritative_roster"]
        if current_roster_evidence["id"] == previous_roster_evidence["id"]:
            state["clean_sweeps"] = []
            state["last_sweep_errors"] = ["authoritative roster snapshot was replayed"]
            return False
        old_roster_observed = _parse_timestamp(
            previous_roster_evidence.get("observed_at"), "authoritative_roster.observed_at", []
        )
        new_roster_observed = _parse_timestamp(
            current_roster_evidence.get("observed_at"), "authoritative_roster.observed_at", []
        )
        if old_roster_observed and new_roster_observed and new_roster_observed <= old_roster_observed:
            state["clean_sweeps"] = []
            state["last_sweep_errors"] = ["authoritative roster observation did not advance"]
            return False
        previous_active = {
            item["workspace_id"]: item
            for item in previous["workspace_roster"] if item["lifecycle"] == "active"
        }
        current_active = {
            item["workspace_id"]: item
            for item in sweep["workspace_roster"] if item["lifecycle"] == "active"
        }
        reused_evidence = _evidence_identities(previous) & _evidence_identities(sweep)
        if reused_evidence:
            state["clean_sweeps"] = []
            state["last_sweep_errors"] = ["proof evidence was replayed between clean sweeps"]
            return False
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
        state["status"] = "certified"
        return True
    return False

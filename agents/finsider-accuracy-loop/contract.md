# Finsider 100% Data Accuracy Contract

This contract is absolute. An agent may identify a flaw in it, but may not weaken it. Contract changes require Daniel's explicit approval.

## Objective

Run independent Claude spec, build, and judge contexts continuously until Finsider has fresh, reproducible, end-to-end data-accuracy proof for every active workspace and every data-bearing product surface.

## What 100% means

Completion requires two consecutive full-application sweeps with different sweep IDs. Each sweep must be independently accepted by the judge and satisfy every condition below:

1. Every active workspace is included. An excluded workspace has an explicit archived, test, or unsupported lifecycle state.
2. `verified_workspaces == active_workspaces`, and `active_workspaces > 0`.
3. `mismatches == 0`, `errors == 0`, `unknowns == 0`, `stale == 0`, and `unresolved_surfaces == 0`.
4. Evidence was observed after the latest completed source sync and latest deployed financial-data code.
5. Every required domain is `proved` with at least one reproducible evidence reference.
6. The onboarding accuracy gate was exercised end to end and is proved.
7. UI, API, export, and agent outputs agree with the same deterministic backend source for identical workspace, period, layer, and dimension inputs.
8. All supported historical periods, transaction layers, report dimensions, and material drilldowns are covered.
9. The authoritative roster has one unique record per workspace. Active workspaces are included; archived, test, and unsupported workspaces have explicit exclusion reasons.
10. No unresolved blocker remains in supervisor state.

An explanation, Jira ticket, owner, open PR, CPA hold, vendor limitation, stale connection, or customer re-auth request is not accuracy. It is a blocker. The loop stays alive and continues other work.

## Required domains

Use these exact machine keys:

1. `source_connections_and_sync_freshness`
2. `tenant_and_workspace_scoping`
3. `chart_of_accounts_and_classification`
4. `report_snapshot_integrity`
5. `profit_and_loss`
6. `balance_sheet`
7. `cash_flow`
8. `adjustments_and_bridge_layers`
9. `cash_proof_and_bank_reconciliation`
10. `kpis_and_derived_metrics`
11. `flux_and_period_comparisons`
12. `quality_of_earnings_reports`
13. `transaction_drilldowns`
14. `dashboards_and_board_reporting`
15. `excel_and_workbook_exports`
16. `ai_cfo_and_agent_numeric_outputs`
17. `deal_and_forecast_models`
18. `api_ui_and_export_parity`
19. `onboarding_accuracy_gate`
20. `rounding_period_key_and_dimension_behavior`

If a domain lacks a deterministic verifier, the missing verifier is the next accuracy defect. Build it before claiming proof.

## Loop roles

- Spec gathers fresh reality and writes one bounded, testable work-unit contract. It does not change code or external state.
- Build performs only that contract. Code uses an isolated worktree and ends in a PR. Operations and proof actions are idempotent.
- Judge starts clean, assumes the result is wrong, and attempts to disprove it with direct evidence.

One rejected code build gets one rework. A second rejection becomes a blocker and the loop advances to other work.

## Required product surfaces

Each full sweep proves these exact machine keys:

`source_api`, `report_api`, `profit_and_loss_ui`, `balance_sheet_ui`, `cash_flow_ui`, `adjustments_ui`, `cash_proof_ui`, `kpi_ui`, `flux_ui`, `quality_of_earnings_ui`, `transaction_drilldowns_ui`, `dashboard_ui`, `board_reporting_ui`, `excel_export`, `ai_cfo`, `finsider_mcp`, `deal_model`, `forecast_model`, and `onboarding`.

Required transaction layers are exactly `original`, `adjusted`, and `bridge`. Required dimensions include `workspace` and `tracking_category`. Period coverage is `all_supported_history`.

## Safety rails

- Never merge or deploy.
- Never write, repair, delete, or resolve production financial records or verification discrepancies.
- Never move money, issue cards, or perform destructive provider actions.
- A verification-run trigger or dry-run recalculation is allowed only when it cannot change customer books.
- A customer-number-changing PR is labelled `NEEDS CPA REVIEW` and held for review.
- Every code fix begins with a reproducing test, runs targeted verification, and preserves tenant and workspace scoping.
- Every user-facing communication follows the Finsider Plain English block, names client companies with workspace IDs, and contains no AI attribution.
- Check for an existing branch, PR, ticket, comment, or verification job carrying the work unit's idempotency key before creating one.
- The supervisor derives the idempotency key from the accepted contract and persists the action intent before execution. External jobs and artifacts return durable receipts for crash-resume polling.
- Child roles have no general shell. They run with phase-specific built-in and MCP allowlists, an all-tool pre-use safety hook, a strict MCP server list, and deployment/production credentials removed from their environment. Tests and delivery use a narrow local service that validates arguments and can only test, inspect, commit, push the current `agent/accuracy-*` branch, and create or reuse an unmerged PR.
- Preserve unrelated dirty files and existing worktrees.

## Writable repositories

One code work unit targets one allowlisted repository:

- `Mitch-be`, base `development`
- `Mitch-fe`, base `development`
- `AI-Agents-CFO`, base `main`
- `finsider-excel-agent`, base `main`
- `finsider-mcp`, base `main`
- `finsider-agents`, base `main`

Read each repository's `AGENTS.md`, `DOMAIN.md`, architecture documents, and local test commands before acting. Backend tests run on Node 20. Never run a production build while the Finsider frontend dev server is active.

## Judge rubric

The score is the weighted sum of:

- Correctness and source reconciliation: 0.40
- Complete contract and application-surface coverage: 0.25
- Regression protection and reproducibility: 0.15
- Freshness and provenance: 0.10
- Safety and delivery discipline: 0.10

`ACCEPT` requires a score of at least `0.90` plus all five hard gates: contract met, regression evidence, source reconciled, freshness, and safety. Tolerance widening, sampling, explained residuals, stale evidence, self-authored evidence without reproduction, or missing surfaces fail a hard gate.

## Full-sweep evidence object

A completion candidate must contain:

- `sweep_id`
- `observed_at`
- `data_watermark`
- `latest_sync_watermark`
- `latest_deploy_watermark`
- `active_workspaces`
- `verified_workspaces`
- `mismatches`
- `errors`
- `unknowns`
- `stale`
- `unresolved_surfaces`
- `onboarding_gate_verified`
- `authoritative_roster`, identified by a fresh immutable source snapshot from `finsider-verification:list_workspaces`
- `workspace_roster`, with a unique ID, name, lifecycle, and inclusion decision for every workspace in that authoritative snapshot; active entries also carry `latest_sync_at`, `verification_id`, and `verified_at`
- `domains`, keyed by all 20 required domain keys, with `{ "status": "proved", "evidence": [ ... ] }`
- `scope.periods`, proving `all_supported_history`
- `scope.layers`, proving `original`, `adjusted`, and `bridge`
- `scope.dimensions`, proving `workspace` and `tracking_category`
- `scope.surfaces`, keyed by every required product surface with proved evidence

Every evidence entry is structured as `{kind, id, source, observed_at, workspace_ids, periods, layers, dimensions, surfaces}`. Lists are non-empty, timestamps include timezones, scope values come from the canonical contract sets, and the combined evidence for each domain and surface covers every active workspace. An evidence timestamp cannot be in the future or after the sweep, and must be at or after both the latest deployment and every referenced workspace's latest sync.

The second clean sweep must retain the same authoritative roster, advance its observation time without regressing global watermarks, use a new authoritative roster snapshot, use a new verification ID with a later verification timestamp for every active workspace, and use no evidence identity from the first sweep. A replay, stale remote branch, aggregate count, opaque evidence string, or roster change cannot complete the sequence.

The supervisor, not an agent, decides whether two accepted sweeps meet completion.

For either sweep to count, the build candidate and judge reproduction must be identical. Completed build receipts and the judge's independently verified evidence list must both contain the authoritative roster snapshot ID, every active workspace verification ID, and every structured proof evidence ID.

# Finsider 100% Data Accuracy Convergence Design

**Date:** 2026-08-08

## North star

For every current and future Finsider workspace, every financial number presented by the application must be a deterministic, reproducible transformation of the authoritative ingested Railz data for the same tenant, connection, accounting method, currency, period, layer, and dimension.

Finsider is accurate only when every customer-facing report, table, drilldown, export, API response, and agent output ties to that canonical source with zero unexplained discrepancy. Missing, stale, incomplete, contradictory, or unsupported source data must fail closed and remain visibly uncertified. It may never be hidden, tolerated, relabelled, or presented as accurate.

This guarantee covers Finsider's ingestion, normalization, classification, calculations, persistence, serialization, and presentation. It cannot guarantee that a customer's underlying accounting books describe economic reality correctly. It guarantees that Finsider faithfully and transparently transforms the selected authoritative source and refuses certification when authoritative sources conflict.

## Canonical data path

Each workspace follows one automatic path:

1. Ingest immutable raw Railz payloads with tenant, connection, sync, period, currency, and source identifiers.
2. Normalize the payload into one canonical financial model with stable account and transaction identities.
3. Derive statements, KPIs, bridges, comparisons, drilldowns, reports, exports, and agent outputs from that model.
4. Verify row-level parity, statement identities, cross-surface parity, tenant isolation, completeness, freshness, and formula invariants.
5. Publish an `accurate` certification only after every required check passes. Otherwise publish the exact blocker and keep the workspace uncertified.

The authoritative workspace roster is dynamic. A newly onboarded workspace automatically enters `pending_sync`, then `verifying`, and cannot become `accurate` until the same contract passes. A roster change invalidates any in-progress fleet certification sequence.

## Agent loop

The loop remains `spec -> build -> judge -> repeat`, with fresh contexts for each role:

- Spec chooses the highest-materiality production mismatch or a required post-deployment proof. It cannot create coverage-only work or duplicate a known baseline.
- Build reproduces the mismatch, changes the actual application path, tests it, and delivers one PR. It never grades itself.
- Judge adversarially reviews the implementation. Before deployment, a correct code change may become only a `CANDIDATE`, never completed accuracy work.
- After authorized merge and deployment, a linked proof reruns the exact production comparison. Only a positive before count moving to zero, with stable or lower skips, stable or larger denominator, fresh evidence, and zero adjacent regressions, can complete the original contract.

Operations and tickets are coordination, not accuracy progress. They never increment completed accuracy work.

## Deterministic convergence gates

The supervisor, not agent prose, enforces:

1. Code PRs enter a durable delivery queue and are not added to completed contract IDs.
2. At most one non-quarantined delivery candidate may wait for review or deployment. While it exists, new code contracts are rejected. The loop may only prove that candidate, report an honest blocked cycle, or run a full sweep when eligible.
3. A mismatch proof linked to a candidate must contain structured production proof: before and after counts, immutable evidence IDs, deployed commit, timestamps, skip counts, denominators, and adjacent-regression count.
4. `after_mismatch_count` must equal zero, `after_skipped_count` cannot exceed before, `after_denominator` cannot shrink, adjacent regressions must be zero, and after evidence cannot reuse before evidence.
5. A full sweep must satisfy the existing content-bound roster and two-independent-sweep contract.
6. A deploy-blocked planner can return a structured blocked result without inventing a ticket, PR, proof run, or code task.
7. Quarantined candidates remain visible but can never be selected for deployment proof until explicitly replaced or cleared.

## Current recovery

The existing pending PR backlog is imported into the delivery queue. PR #1130 is quarantined as unsafe. Open CPA-review candidates and merged-but-unproved candidates are retained as pending work. The old completed-contract history moves to an explicitly historical list, while the new proof sequence starts empty. No pre-deployment acceptance can count as accuracy completion.

The loop does not autonomously merge or deploy financial code. Institutional-grade accuracy requires review separation. It continuously monitors the delivery gate, resumes proof immediately after an authorized deployment, and keeps the exact production mismatch open until zero is independently reproduced.

## Completion

The supervisor declares the current roster certified only after two independent full-fleet sweeps prove every active workspace accurate across all required surfaces and there are no unresolved blockers or pending candidates. It does not stop. It keeps running fresh dynamic-roster certification sweeps; a changed roster or failed invariant immediately returns the state to running and restarts the two-sweep sequence. Future workspaces therefore cannot silently enter the product without certification.

Until those conditions are met, the honest accuracy certification is incomplete regardless of PR count, ticket count, agent confidence, or elapsed cycles.

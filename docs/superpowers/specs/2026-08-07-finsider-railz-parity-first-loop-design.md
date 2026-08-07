# Finsider Railz Parity-First Accuracy Loop Design

**Date:** 2026-08-07

## Objective

Run the Finsider accuracy supervisor continuously against concrete, customer-visible financial mismatches until the application reproduces the authoritative ingested Railz data without unexplained discrepancy across statements, calculations, APIs, UI, exports, and AI outputs.

The loop must improve the application and its data path. It must not spend cycles adding verifier categories while known financial mismatches remain.

## Accuracy contract

For accounting statements, the source of truth is the authoritative Railz report payload for the same workspace, connection, accounting method, currency, period, and reconstruction policy.

For transaction surfaces, the source of truth is the complete, tenant-scoped, deduplicated set of ingested Railz records. A disagreement between bank and accounting sources is a real unresolved discrepancy. The loop may not hide it, relabel it, or count it as accurate merely because an explanation exists.

Zero discrepancy means exact equality under the product's explicitly documented financial rounding rules. Skipped checks, warnings, tolerances, stale evidence, vendor limitations, or explained mismatches do not count as zero.

## Loop behavior

Each ordinary cycle must start with a measured mismatch greater than zero and end with that same scoped mismatch at zero, with regression evidence for adjacent surfaces. The planner prioritizes the highest-materiality and broadest-impact discrepancies first.

Allowed work kinds are:

- `application_fix`: change the Railz ingestion or downstream application path.
- `data_fix`: perform or coordinate an explicitly authorized, auditable reconciliation operation.
- `mismatch_proof`: rerun existing measurements after a shipped fix or safe data operation.
- `full_sweep`: execute the existing end-to-end accuracy suite after all known mismatches are zero.

There is no `verifier` work kind. New verification code is allowed only when an existing measurement is demonstrably incorrect and directly blocks remediation of a concrete mismatch. Coverage-only work is not selectable.

The planner must record the baseline mismatch count, target count of zero, evidence identifiers, and affected application paths. The builder must modify the actual Railz-to-customer data path unless the contract documents a measurement regression. The judge accepts only when before-and-after receipts prove the scoped mismatch moved from greater than zero to zero without regression.

## Crash and duplicate safety

Changing the global accuracy contract invalidates any in-flight cycle. The supervisor resets the current phase, active contract, action intent, worktree pointer, retry state, and phase artifacts while preserving historical blockers, coverage, ledger, and cycle count.

Accepted contract IDs are durable loop state and may never be reused. This prevents a completed contract from colliding with an old worktree when a planner slightly changes the title.

The loop remains PR-only for financial code. It does not auto-merge, deploy, alter raw books, or mutate customer financial records. A genuine source conflict remains a blocker until it is corrected or reconciled through an authorized operation.

## Completion

Completion requires all existing mismatch measurements to be zero and two fresh, independent full sweeps with no skipped, warned, stale, tolerated, or unexplained financial discrepancy. The loop must keep running while any mismatch or evidence gap remains.

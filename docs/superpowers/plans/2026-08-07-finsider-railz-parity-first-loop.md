# Finsider Railz Parity-First Accuracy Loop Implementation Plan

**Goal:** Redirect the continuous supervisor from coverage work to concrete Railz/application mismatch remediation, recover it from the current C51 worktree collision, and prove the new policy in the live runtime.

**Architecture:** Keep the existing three-file durable runtime. Strengthen the work contract with structured mismatch fields, reset in-flight state when the global contract changes, and retain accepted contract IDs in `STATE.json` so completed work cannot be selected again.

## Task 1: Specify the parity-first operating contract

- Update the global contract and agent prompts with the authoritative Railz parity rules.
- Remove the rule that makes a missing verifier the next defect.
- Require concrete before/after mismatch receipts for acceptance.
- Verify the written policy contains no coverage-only selection path.

## Task 2: Reproduce the stale-cycle and duplicate-ID failures

- Add a supervisor test with an active build cycle, retry state, action intent, and worktree pointer.
- Change the global contract and assert the active cycle resets while history remains.
- Add a test proving a previously accepted contract ID cannot be selected again.
- Run the focused tests and confirm they fail for the expected reasons.

## Task 3: Implement crash-resume reconciliation

- Reset the current cycle in `ensure_runtime` when the contract hash changes.
- Persist accepted contract IDs in the existing state file.
- Migrate prior accepted IDs from accepted ledger entries where possible.
- Validate proposed contracts against the completed-ID set.
- Run focused tests until green.

## Task 4: Enforce mismatch-bearing work contracts

- Add structured work kind, baseline mismatch count, zero target, evidence IDs, and application paths to the spec schema.
- Reject ordinary work with a zero baseline or no application path.
- Permit a zero baseline only for full sweeps after known mismatches are cleared.
- Update test fixtures and add policy regression tests.

## Task 5: Verify and reactivate

- Run the full accuracy-loop unit suite.
- Run static or syntax checks used by the repository.
- Install the updated supervisor, stop the stale process safely, and reactivate it.
- Inspect runtime state and ledger to prove the stale C51 build is gone and the next selected contract targets a concrete financial mismatch.

## Task 6: Record the operational change

- Update the Finsider Brain project/audit record with the new parity-first contract, live recovery result, and remaining accuracy blockers.
- Report shipped changes, test evidence, live run status, and the honest current certification percentage.

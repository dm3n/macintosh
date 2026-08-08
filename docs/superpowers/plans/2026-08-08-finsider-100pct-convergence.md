# Finsider 100% Data Accuracy Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the continuous accuracy supervisor count only deployed, independently reproduced zero-mismatch outcomes toward Finsider's 100% current-and-future workspace north star.

**Architecture:** Preserve the three-file durable runtime and existing spec/build/judge roles. Add a delivery-candidate queue to `STATE.json`, distinguish pre-deployment `CANDIDATE` from post-deployment `ACCEPT`, and enforce structured production-proof invariants in Python rather than prompts.

**Tech Stack:** Python 3.9, `unittest`, launchd, Claude Code structured output, GitHub CLI, Finsider verification MCP.

## Global Constraints

- No autonomous merge, deploy, force-push, or production financial-record mutation.
- No open PR, ticket, explanation, skipped check, or tolerated residual counts as accuracy.
- One new delivery candidate may be in flight at a time; the imported legacy backlog is the temporary exception. Closed unsafe PRs remain in separate quarantine history.
- Every current and future authoritative active workspace is in scope.
- Certification requires two fresh independent full-fleet sweeps with zero mismatches, errors, unknowns, stale data, unresolved surfaces, blockers, or pending candidates. The daemon then continues dynamic-roster sweeps forever.

---

### Task 1: Durable candidate and proof state

**Files:**
- Modify: `agents/finsider-accuracy-loop/accuracy_loop/model.py`
- Test: `agents/finsider-accuracy-loop/tests/test_model.py`

**Interfaces:**
- Produces: `delivery_candidates: list`, `quarantined_deliveries: list`, `completed_operation_ids: list` defaults in every loaded state.

- [ ] Write tests proving new states and existing v2 states expose both lists.
- [ ] Run the focused model tests and observe the missing-key failure.
- [ ] Add the two defaults without increasing the top-level durable-file count.
- [ ] Run the focused model tests green.

### Task 2: Candidate versus accuracy acceptance

**Files:**
- Modify: `agents/finsider-accuracy-loop/accuracy_loop/supervisor.py`
- Test: `agents/finsider-accuracy-loop/tests/test_supervisor.py`

**Interfaces:**
- Produces: `_judge_candidate_ready(state, result) -> bool`, `_queue_delivery_candidate(state, work_unit, build, result)`, `CANDIDATE` judge verdict.

- [ ] Write a failing test proving an accepted open code PR cannot enter `completed_contract_ids`.
- [ ] Write a failing test proving a `CANDIDATE` verdict queues the PR and returns to spec.
- [ ] Run both tests and observe the old completion behavior/schema failure.
- [ ] Add the candidate schema, validation, queue record, and `CANDIDATE-READY` ledger path.
- [ ] Run both tests green.

### Task 3: Structured production proof

**Files:**
- Modify: `agents/finsider-accuracy-loop/accuracy_loop/supervisor.py`
- Test: `agents/finsider-accuracy-loop/tests/test_supervisor.py`

**Interfaces:**
- Produces: `_production_proof_accepts(work_unit, result) -> bool` and `production_proof` judge schema.
- Consumes: contract fields `depends_on_contract_id` and `baseline_mismatch_count`.

- [ ] Write failing tests for missing production proof, nonzero after count, increased skips, shrunken denominator, reused evidence, and adjacent regressions.
- [ ] Write a passing-intent test for positive-before to zero-after proof linked to a queued candidate.
- [ ] Run focused tests and observe the old boolean-gate acceptance.
- [ ] Implement the minimal structured proof validator and candidate removal/completion path.
- [ ] Run focused tests green.

### Task 4: WIP and honest blocked cycles

**Files:**
- Modify: `agents/finsider-accuracy-loop/accuracy_loop/supervisor.py`
- Modify: `agents/finsider-accuracy-loop/prompts/spec.md`
- Test: `agents/finsider-accuracy-loop/tests/test_supervisor.py`

**Interfaces:**
- Produces: nullable blocked spec contract, `DEPLOY-BLOCKED` ledger outcome, one-candidate WIP validation.

- [ ] Write a failing test proving new code is rejected while a non-quarantined candidate exists.
- [ ] Write a failing test proving a structured blocked spec performs no build, ticket, PR, or proof run.
- [ ] Run the focused tests red.
- [ ] Implement blocked spec handling and deterministic WIP validation.
- [ ] Update the spec prompt to use the structured blocked result.
- [ ] Run the focused tests green.

### Task 5: Operations and full-sweep integrity

**Files:**
- Modify: `agents/finsider-accuracy-loop/accuracy_loop/supervisor.py`
- Test: `agents/finsider-accuracy-loop/tests/test_supervisor.py`

**Interfaces:**
- Produces: `COORDINATED` operation outcome that does not count as accuracy; full-sweep acceptance requires a corroborated sweep object.

- [ ] Write failing tests proving an operations ticket does not enter completed accuracy IDs and a full-sweep contract cannot complete without a corroborated sweep.
- [ ] Run focused tests red.
- [ ] Implement both deterministic gates.
- [ ] Run focused tests green.

### Task 6: North-star contracts and prompts

**Files:**
- Modify: `agents/finsider-accuracy-loop/contract.md`
- Modify: `agents/finsider-accuracy-loop/prompts/spec.md`
- Modify: `agents/finsider-accuracy-loop/prompts/build.md`
- Modify: `agents/finsider-accuracy-loop/prompts/judge.md`

**Interfaces:**
- Documents: dynamic current/future roster, canonical Railz data path, candidate/delivery/proof lifecycle, fail-closed source conflicts.

- [ ] Replace pre-deployment acceptance language with candidate language.
- [ ] Require linked production-proof fields from build and judge roles.
- [ ] State the current-and-future workspace north star verbatim in all role contexts.
- [ ] Run `git diff --check` and inspect for contradictions with safety rails.

### Task 7: Full verification and live activation

**Files:**
- Modify only if a failing verification requires it.

**Interfaces:**
- Consumes: canonical `install.sh --activate` workflow.

- [ ] Run the full accuracy-loop test suite.
- [ ] Run Python compilation and `make validate`.
- [ ] Commit the implementation with no AI attribution.
- [ ] Merge to canonical `main`, push, and rerun the full suite on the merged result.
- [ ] Gracefully stop and reactivate `com.finsider.accuracy-loop` from canonical source.
- [ ] While the daemon is stopped, close unsafe PR #1130, import the current open and merged-but-unproved backlog into `delivery_candidates`, and retain #1130 in `quarantined_deliveries`.
- [ ] Verify live state has zero retries, no stale active contract, a visible delivery queue, no pre-deployment PR counted as newly completed accuracy work, and no successful-certification exit path.

### Task 8: Brain continuity

**Files:**
- Modify: `Brain/Memory/status_finsider_accuracy_loop_continuous_2026_08_06.md`

**Interfaces:**
- Records: new north star, hard acceptance gates, live activation evidence, remaining human-controlled release queue.

- [ ] Add the convergence architecture and activation result to the existing memory note.
- [ ] Report the honest certification state without converting pending candidates into accuracy progress.

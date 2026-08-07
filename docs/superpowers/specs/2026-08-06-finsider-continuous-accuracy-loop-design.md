# Finsider Continuous Accuracy Loop Design

**Date:** 2026-08-06
**Status:** Approved by Daniel on 2026-08-06
**Owner:** Daniel Edgar

## Objective

Run three fresh Claude contexts continuously, in strict `spec -> build -> judge` order, until Finsider has complete and independently verified data-accuracy evidence across every active workspace and every data-bearing application surface.

The loop may not call a mismatch accurate because it is explained, ticketed, externally owned, or waiting on a human. Those states remain incomplete. The loop stays alive, keeps advancing other work, and waits for the blocking evidence to change.

## Current problem

The existing harness does not meet this objective:

- `com.finsider.accuracy-loop` starts one monolithic Claude prompt every 30 minutes.
- `com.finsider.tieout-loop` measures every two hours and deep-reads at most eight workspaces.
- The current terminal contract accepts explained or ticketed mismatches as terminal.
- Planner, builder, and judge are nested inside one orchestrator context, so role separation is not mechanically enforced.
- The observed fleet baseline on 2026-08-06 was 30 workspaces, 0 accurate, 19 with issues, 2 stale, and 6 unknown.

The replacement must remove fixed scheduling, remove the eight-workspace proof ceiling, enforce independent roles, and make completion a deterministic supervisor decision.

## Definition of 100% data accuracy

Finsider reaches the proof state only when all of the following are true:

1. Every active workspace is included. Archived, test, and unsupported workspaces require an explicit lifecycle classification before exclusion.
2. Every included workspace has a fresh successful verification after its latest completed source sync and after the latest deployed code affecting financial data.
3. Every included workspace has zero errors, zero unresolved mismatches, zero unknown checks, and zero stale connections or stale snapshots.
4. Every supported historical period, transaction layer, report dimension, and material drilldown represented in the application is covered by the verification evidence.
5. Every required accuracy domain below is `proved` with named, reproducible evidence.
6. UI, API, export, and agent surfaces agree with the same deterministic backend source for the same workspace, period, layer, and dimension.
7. The onboarding accuracy gate has been exercised end to end and rejects or flags any workspace that lacks a complete proof state.
8. An independent judge re-runs or directly inspects the decisive evidence and accepts every hard gate.
9. Two consecutive full-application sweeps satisfy these conditions with different sweep IDs. The second sweep must be at least as fresh as the first and must include no regression.

The required accuracy domains are:

1. Source connections and sync freshness
2. Tenant and workspace scoping
3. Chart of accounts and classification
4. Report snapshot integrity
5. Profit and loss
6. Balance sheet
7. Cash flow
8. Adjustments and bridge layers
9. Cash proof and bank reconciliation
10. KPIs and derived metrics
11. Flux and period comparisons
12. Quality of Earnings reports
13. Transaction drilldowns
14. Dashboards and board reporting
15. Excel and workbook exports
16. AI CFO and agent numeric outputs
17. Deal and forecast models
18. API, UI, and export parity
19. Onboarding accuracy gate
20. Rounding, period-key, and dimension behavior

If a domain cannot yet produce deterministic evidence, that is an instrumentation gap. The loop builds the missing verifier before it can mark the domain proved.

## Architecture

One persistent Python supervisor is owned by launchd. It stays in memory and advances the next phase immediately after the prior phase finishes. launchd restarts it after crashes, but a clean exit after the deterministic completion gate does not restart.

Each phase launches a new headless Claude Code process using the authenticated Claude subscription, `claude-sonnet-4-6`, maximum effort, no saved conversation, and a phase-specific prompt and JSON schema.

### Spec agent

The spec agent gathers the freshest available evidence from the verification MCP, GitHub, Jira, the application repositories, and the prior state. It inventories unknown coverage rather than limiting itself to the existing tie-out queue. It selects one bounded work unit and writes a testable contract. It never edits code, opens PRs, changes Jira, or mutates production.

The selected action is exactly one of:

- `code`: implement or extend a deterministic fix or verifier in one repository.
- `operations`: perform one safe, idempotent coordination action such as opening a data backfill, re-auth, lifecycle, or CPA-review ticket.
- `proof`: run or collect fresh verification evidence without changing financial data.

### Build agent

The build agent receives only the approved work-unit contract and current state. For a code action, the supervisor gives it an isolated Git worktree based on the target repository's configured base branch. It reproduces the failure first, makes the smallest change, runs the targeted checks, pushes a uniquely keyed branch, and opens a PR. It never merges or deploys.

For operations and proof actions, it performs only the action authorized by the contract. Production financial data changes, discrepancy resolution, money movement, and destructive actions are forbidden. Verification-run triggers are allowed because they create evidence without changing customer books.

### Judge agent

The judge starts in a third, clean context and assumes the build is wrong. It reads the contract, diff, tests, source evidence, and customer-facing path. It tries to disprove correctness, freshness, scope, parity, and safety. It cannot edit code, merge, deploy, mutate production data, resolve findings, or create replacement evidence.

The judge returns `ACCEPT`, `REJECT`, or `BLOCKED`, a score in `[0,1]`, hard-gate results, verified evidence, and specific rework instructions. An accept requires every hard gate and a score of at least `0.90`. A number-moving change must also be labelled for CPA review.

One rejected code build gets one fresh rework context in the same isolated worktree. A second rejection is recorded as blocked, not silently retried or called complete. The supervisor immediately moves to the next drivable work unit.

## Supervisor state and crash recovery

All durable loop state fits in three files under `~/finsider-platform/.accuracy-supervisor/`:

- `CONTRACT.md`: the immutable global proof contract and current work-unit contract.
- `STATE.json`: schema version, phase, cycle, active contract, worktree, attempts, accepted evidence, coverage status, blockers, clean-sweep history, and retry state.
- `LEDGER.md`: append-only human-readable phase outcomes and links.

Raw Claude outputs live in a bounded trace directory for debugging and are not authoritative state. State writes are atomic. A file lock prevents multiple supervisors. On restart, the supervisor resumes the recorded phase. Every external action uses the contract ID as an idempotency key, and each prompt requires checking for an existing branch, PR, ticket, comment, or verification job before creating one.

## Back-to-back execution

There is no `StartInterval` and no two-hour measurement dependency.

- After an accepted, rejected, routed, or blocked work unit, the next spec phase starts immediately.
- When a verification job is running, the supervisor condition-polls that job instead of starting a duplicate.
- When only human or vendor blockers remain, the process stays alive and rechecks evidence at a bounded interval of at most five minutes.
- Authentication, rate-limit, model-overload, and transient-tool failures use bounded exponential backoff, then resume the same phase.
- The supervisor exits cleanly only after two distinct accepted full-application proof sweeps pass the deterministic completion gate.

This is continuous execution, not a faster cron job.

## Repositories and delivery

The loop may inspect every Finsider repository. A code contract targets one repository and one PR at a time. Initial writable targets are:

- `Mitch-be`, base `development`
- `Mitch-fe`, base `development`
- `AI-Agents-CFO`, base `main`
- `finsider-excel-agent`, base `main`
- `finsider-mcp`, base `main`
- `finsider-agents`, base `main`

The supervisor harness itself is versioned in `homelab-macintosh`. Runtime financial changes are delivered only through reviewable PRs in the target product repository.

## Safety contract

- Never auto-merge or deploy.
- Never write or repair production financial records.
- Never resolve or delete verification discrepancies.
- Never move money, issue cards, or perform destructive provider actions.
- Triggering read-only verification and dry-run recalculation is allowed.
- Customer-number-changing changes are held for CPA review.
- Every user-facing communication follows the Finsider Plain English block and names client companies with workspace IDs.
- Every code fix includes a reproducing test and targeted verification.
- No AI attribution appears in commits, PRs, or tickets.
- Existing active worktrees and unrelated dirty files are preserved.

## Failure handling

- Invalid or unparseable agent output records a phase failure and retries the same phase with backoff.
- Claude subscription exhaustion or authentication failure never marks work complete. The loop waits and resumes.
- A stale or dead child process is terminated by the supervisor timeout and recorded.
- A worktree is removed only after the branch is clean and its work is pushed or deliberately abandoned with evidence in state.
- The old periodic jobs are unloaded only after their active processes exit and the new supervisor passes its local tests.
- launchd uses `KeepAlive.SuccessfulExit = false`: crashes restart, deterministic completion does not.

## Verification strategy

The supervisor is built test-first with standard-library Python tests covering:

- atomic state creation and crash resume for every phase;
- exact completion-gate rejection of mismatches, errors, unknowns, stale data, missing domains, stale watermarks, reused sweep IDs, rejected judges, and missing onboarding proof;
- immediate phase transition without a fixed schedule;
- bounded wait behavior for in-flight and external blockers;
- structured-output parsing and retry behavior;
- idempotent worktree and external-action handoffs;
- signal handling and child cleanup;
- launchd plist validity and clean-exit restart semantics.

Activation verification proves the legacy 30-minute and two-hour jobs are unloaded, the new service is running, the state files are valid, and the first live spec phase has started. Activation does not claim Finsider is accurate. The state and ledger report the actual proof gap until the completion gate passes.

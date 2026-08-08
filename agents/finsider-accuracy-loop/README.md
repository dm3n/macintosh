# Finsider Continuous Accuracy Loop

Persistent Claude `spec -> build -> judge` supervisor for proving Finsider data accuracy across the complete workspace fleet and every data-bearing product surface.

This is not a cron job. The next phase starts as soon as the prior phase ends. The process waits only for an in-flight verification job, a transient Claude/tool failure, or external evidence. Such waits are capped at five minutes.

## Safety

- Code changes end in PRs. The loop never merges or deploys.
- Production financial data and verification findings are read-only.
- Verification triggers and dry runs are allowed only when they cannot change customer books.
- Customer-number-changing work is held as `NEEDS CPA REVIEW`.
- Each Claude role has a fresh context. Spec and judge cannot edit files. No role can spawn nested agents.
- Claude runs without permission bypass or general shell access, with a deny-by-default phase tool policy, a strict MCP list, an all-tool safety hook, and production/deployment credentials removed from child environments. A narrow local service handles approved tests and safe Git/PR delivery. Tests run in a sanitized, network-denied macOS sandbox; automated delivery rejects CI workflow, deployment, and infrastructure paths.
- The supervisor, not Claude, decides certification.

## Certification gate

The current dynamic roster becomes certified only after two different, independently judged full-application sweeps prove:

- the authoritative workspace roster is complete, every active workspace is included and fresh, and every exclusion has an explicit lifecycle reason;
- zero mismatches, errors, unknowns, stale items, or unresolved surfaces;
- all 20 contract domains and every required product surface have structured, reproducible evidence covering every active workspace;
- all supported periods, layers, dimensions, drilldowns, APIs, UIs, exports, and agent outputs agree;
- the onboarding accuracy gate works end to end.
- the second sweep uses a different immutable verification run for every active workspace.

Tickets, explanations, owners, stale connections, unsupported providers, open PRs, and CPA holds remain blockers. They never count as accuracy.

The process does not exit after certification. It continues fresh fleet sweeps forever. A roster change, newly onboarded workspace, mismatch, stale source, skipped check, missing surface, or failed invariant immediately returns the state to running and restarts the two-sweep sequence.

## Install and activate

```bash
./agents/finsider-accuracy-loop/install.sh --check
./agents/finsider-accuracy-loop/install.sh --activate
```

Activation refuses while the legacy fix or tie-out process is active. It validates the full harness before unloading anything, gracefully stops an older supervisor, atomically refreshes the versioned contract, installs the persistent plist, and starts the supervisor. A failed launchd handoff restores the prior plist. A contract change invalidates any prior clean-sweep sequence.

## Runtime state

Authoritative state is exactly:

```text
/Users/dm3n/finsider-platform/.accuracy-supervisor/CONTRACT.md
/Users/dm3n/finsider-platform/.accuracy-supervisor/STATE.json
/Users/dm3n/finsider-platform/.accuracy-supervisor/LEDGER.md
```

Raw Claude output and isolated worktrees are debug artifacts under `traces/` and `worktrees/`. They are not authoritative state.

Inspect current proof status:

```bash
python3 -m json.tool /Users/dm3n/finsider-platform/.accuracy-supervisor/STATE.json
tail -100 /Users/dm3n/finsider-platform/.accuracy-supervisor/LEDGER.md
```

Inspect service status:

```bash
launchctl print gui/$(id -u)/com.finsider.accuracy-loop
ps -axo pid,ppid,etime,command | rg 'finsider-accuracy-loop/run.py|claude -p'
```

Read the newest raw traces when debugging:

```bash
ls -lt /Users/dm3n/finsider-platform/.accuracy-supervisor/traces | head
```

## Pause and resume

Pause after the active Claude child receives a termination signal:

```bash
launchctl kill SIGTERM gui/$(id -u)/com.finsider.accuracy-loop
```

Resume the loaded service:

```bash
launchctl kickstart -k gui/$(id -u)/com.finsider.accuracy-loop
```

Unload it completely:

```bash
launchctl bootout gui/$(id -u)/com.finsider.accuracy-loop
```

The recorded phase resumes after a restart. Do not hand-edit `STATE.json` while the service is running.

## Delivery behavior

Code work is isolated under the runtime worktree directory. The branch name starts with `agent/accuracy-` and the PR targets the configured repository base branch. The work unit's idempotency key is used to find an existing branch, PR, ticket, comment, or verification job after a crash.

A passing code PR is queued as a delivery `CANDIDATE`; it is not completed accuracy. The queue blocks new code until a linked post-deployment proof independently reproduces a positive before count moving to exactly zero with no additional skips, denominator shrinkage, recycled evidence, or adjacent regressions. The supervisor also proves the candidate commit is contained in the current production ref and binds it to a successful trusted deployment receipt. Candidate creation and deployment proof invalidate older clean sweeps. Operations artifacts are recorded separately and never count as accuracy.

Unsafe closed PRs remain visible in `quarantined_deliveries` but are not active candidates. Backlog import takes the same process lock as the daemon and refuses to run unless the service is stopped.

Code delivery is limited to repositories with a machine-verifiable production-release policy. The Excel surface remains mandatory in every fleet sweep, but `finsider-excel-agent` is operations-only until its local repository is connected to Git and its Vercel/AppSource release exposes a trusted production receipt. This prevents an Excel code candidate from entering a queue it can never prove or clear.

The legacy state under `.accuracy-fix-loop` and the old tie-out state under `~/.claude/scripts/tieout-loop` are retained as historical input. They are not deleted and cannot satisfy the new completion gate.

# Finsider Continuous Accuracy Loop

Persistent Claude `spec -> build -> judge` supervisor for proving Finsider data accuracy across the complete workspace fleet and every data-bearing product surface.

This is not a cron job. The next phase starts as soon as the prior phase ends. The process waits only for an in-flight verification job, a transient Claude/tool failure, or external evidence. Such waits are capped at five minutes.

## Safety

- Code changes end in PRs. The loop never merges or deploys.
- Production financial data and verification findings are read-only.
- Verification triggers and dry runs are allowed only when they cannot change customer books.
- Customer-number-changing work is held as `NEEDS CPA REVIEW`.
- Each Claude role has a fresh context. Spec and judge cannot edit files. No role can spawn nested agents.
- The supervisor, not Claude, decides completion.

## Completion gate

The loop exits cleanly only after two different, independently judged full-application sweeps prove:

- every active workspace is included and fresh;
- zero mismatches, errors, unknowns, stale items, or unresolved surfaces;
- all 20 contract domains have reproducible evidence;
- all supported periods, layers, dimensions, drilldowns, APIs, UIs, exports, and agent outputs agree;
- the onboarding accuracy gate works end to end.

Tickets, explanations, owners, stale connections, unsupported providers, open PRs, and CPA holds remain blockers. They never count as accuracy.

## Install and activate

```bash
./agents/finsider-accuracy-loop/install.sh --check
./agents/finsider-accuracy-loop/install.sh --activate
```

Activation refuses while the legacy fix or tie-out process is in the middle of a pass. It unloads both periodic launchd jobs, initializes the three-file state, installs the persistent plist, and starts the supervisor.

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

The legacy state under `.accuracy-fix-loop` and the old tie-out state under `~/.claude/scripts/tieout-loop` are retained as historical input. They are not deleted and cannot satisfy the new completion gate.

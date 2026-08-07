# Finsider Continuous Accuracy Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Finsider's periodic, permissive accuracy jobs with one persistent Claude spec/build/judge supervisor that runs back to back and exits only after two independently accepted full-application proof sweeps.

**Architecture:** A standard-library Python package owns atomic three-file state, fresh Claude CLI processes, isolated target-repository worktrees, phase recovery, and a deterministic completion gate. launchd keeps the supervisor alive after failures but does not restart it after a clean proof-complete exit.

**Tech Stack:** Python 3.9 standard library, `unittest`, Claude Code CLI, Git/GitHub CLI, launchd, Bash.

## Global Constraints

- The loop completion definition is the full contract in `docs/superpowers/specs/2026-08-06-finsider-continuous-accuracy-loop-design.md`.
- Durable runtime state is exactly `CONTRACT.md`, `STATE.json`, and `LEDGER.md` under `/Users/dm3n/finsider-platform/.accuracy-supervisor`.
- Every phase uses a fresh `claude-sonnet-4-6` context with maximum effort and structured output.
- Never auto-merge, deploy, mutate production financial data, resolve discrepancies, or perform destructive provider actions.
- Code actions target exactly one allowlisted Finsider repository and produce a PR.
- Customer-number-changing code is labelled `NEEDS CPA REVIEW`.
- No AI attribution appears in commits, PRs, tickets, or comments.
- The old launchd jobs are not unloaded until their active processes have exited and local verification passes.

---

## File map

- `agents/finsider-accuracy-loop/accuracy_loop/model.py`: runtime state defaults, atomic persistence, phase transitions, proof-sweep validation, and completion decision.
- `agents/finsider-accuracy-loop/accuracy_loop/claude.py`: fresh Claude process execution, JSON-schema output extraction, timeouts, trace capture, and transient-failure classification.
- `agents/finsider-accuracy-loop/accuracy_loop/workspace.py`: repository allowlist and isolated worktree lifecycle.
- `agents/finsider-accuracy-loop/accuracy_loop/supervisor.py`: persistent spec/build/judge state machine, crash resume, one rework, backoff, condition waits, and signal handling.
- `agents/finsider-accuracy-loop/accuracy_loop/__init__.py`: package marker and public version.
- `agents/finsider-accuracy-loop/run.py`: launchd entrypoint.
- `agents/finsider-accuracy-loop/contract.md`: exact global accuracy contract seeded into runtime state.
- `agents/finsider-accuracy-loop/prompts/spec.md`: read-only fleet/application investigator and one-work-unit contract writer.
- `agents/finsider-accuracy-loop/prompts/build.md`: idempotent code/operations/proof actor.
- `agents/finsider-accuracy-loop/prompts/judge.md`: read-only adversarial evaluator and completion-proof auditor.
- `agents/finsider-accuracy-loop/com.finsider.accuracy-loop.plist`: persistent launchd definition.
- `agents/finsider-accuracy-loop/install.sh`: preflight, state initialization, legacy-job retirement, plist installation, and bootstrap.
- `agents/finsider-accuracy-loop/README.md`: operations, safety, state, pause/resume, trace reading, and proof status.
- `agents/finsider-accuracy-loop/tests/`: behavior tests for the four Python modules and installer artifacts.

### Task 1: Atomic state and deterministic completion gate

**Files:**
- Create: `agents/finsider-accuracy-loop/accuracy_loop/__init__.py`
- Create: `agents/finsider-accuracy-loop/accuracy_loop/model.py`
- Create: `agents/finsider-accuracy-loop/tests/test_model.py`

**Interfaces:**
- Produces: `new_state() -> dict`, `load_state(path) -> dict`, `save_state(path, state) -> None`, `advance_phase(state, phase) -> dict`, `record_accepted_sweep(state, sweep) -> bool`, and `REQUIRED_DOMAINS`.
- `record_accepted_sweep` returns `True` only when the second distinct, complete, non-regressing sweep is accepted.

- [ ] **Step 1: Write failing state and completion tests**

```python
def test_two_distinct_complete_sweeps_finish():
    state = new_state()
    assert record_accepted_sweep(state, complete_sweep("sweep-1")) is False
    assert record_accepted_sweep(state, complete_sweep("sweep-2")) is True

def test_unknown_or_missing_domain_never_finishes():
    state = new_state()
    bad = complete_sweep("sweep-1")
    bad["unknowns"] = 1
    assert record_accepted_sweep(state, bad) is False
    assert state["clean_sweeps"] == []
```

- [ ] **Step 2: Run the tests and confirm missing-module failure**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_model.py' -v`

Expected: import failure for `accuracy_loop.model`.

- [ ] **Step 3: Implement the minimal state model**

Use atomic `json.dump` to a sibling temporary file followed by `os.replace`. Validate exact domain coverage, non-empty evidence per domain, onboarding proof, zero bad counts, fresh watermark fields, unique sweep IDs, and judge acceptance before appending a clean sweep. Preserve at most the two latest accepted clean sweeps.

- [ ] **Step 4: Run the focused tests green**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_model.py' -v`

- [ ] **Step 5: Commit**

```bash
git add agents/finsider-accuracy-loop/accuracy_loop agents/finsider-accuracy-loop/tests/test_model.py
git commit -m "feat: add accuracy proof state model"
```

### Task 2: Claude phase runner with structured output and bounded failures

**Files:**
- Create: `agents/finsider-accuracy-loop/accuracy_loop/claude.py`
- Create: `agents/finsider-accuracy-loop/tests/test_claude.py`

**Interfaces:**
- Consumes: prompt text, JSON schema, working directory, trace directory, phase name, and injectable command runner.
- Produces: `ClaudeRunner.run(phase, prompt, schema, cwd) -> dict` and typed `AgentFailure(transient: bool, message: str)`.

- [ ] **Step 1: Write failing parser and command tests**

```python
def test_extracts_structured_output_from_claude_envelope():
    raw = json.dumps({"type": "result", "structured_output": {"decision": "code"}})
    assert extract_structured_output(raw) == {"decision": "code"}

def test_command_uses_fresh_max_effort_subscription_context():
    command = build_command("{}")
    assert command[:4] == [CLAUDE_BIN, "-p", "--model", "claude-sonnet-4-6"]
    assert "--effort" in command and "max" in command
    assert "--no-session-persistence" in command
```

- [ ] **Step 2: Run the tests and confirm missing-module failure**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_claude.py' -v`

- [ ] **Step 3: Implement the runner**

Strip `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` so the Claude subscription and keychain MCP authentication are used. Execute with `--output-format json`, `--json-schema`, `--effort max`, and `--no-session-persistence`. Write raw stdout and stderr to a timestamped trace, parse `structured_output`, and classify authentication, rate-limit, overload, timeout, and malformed-output failures without declaring completion.

- [ ] **Step 4: Run the focused tests green**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_claude.py' -v`

- [ ] **Step 5: Commit**

```bash
git add agents/finsider-accuracy-loop/accuracy_loop/claude.py agents/finsider-accuracy-loop/tests/test_claude.py
git commit -m "feat: add isolated Claude phase runner"
```

### Task 3: Isolated product-repository worktrees

**Files:**
- Create: `agents/finsider-accuracy-loop/accuracy_loop/workspace.py`
- Create: `agents/finsider-accuracy-loop/tests/test_workspace.py`

**Interfaces:**
- Produces: `REPOSITORIES`, `create_worktree(repo_key, contract_id, title, runtime_dir) -> Worktree`, `inspect_worktree(worktree) -> dict`, and `remove_clean_worktree(worktree) -> bool`.
- Repository entries provide absolute checkout path and base branch.

- [ ] **Step 1: Write failing allowlist and real temporary-Git tests**

```python
def test_rejects_repository_outside_allowlist():
    with self.assertRaises(ValueError):
        create_worktree("unknown", "ACC-1", "bad", self.runtime)

def test_creates_branch_from_configured_base_in_isolated_path():
    worktree = create_worktree("fixture", "ACC-1", "cash-proof", self.runtime,
                               repositories={"fixture": Repo(self.repo, "development")})
    self.assertEqual(current_branch(worktree.path), "agent/accuracy-acc-1-cash-proof")
```

- [ ] **Step 2: Run the tests and confirm missing-module failure**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_workspace.py' -v`

- [ ] **Step 3: Implement minimal worktree management**

Fetch the configured base, reuse an existing matching worktree after a crash, otherwise create one under the runtime trace/worktree area. Refuse branch names or paths outside the allowlist. Remove only a clean worktree; keep dirty or unpushed work for inspection.

- [ ] **Step 4: Run the focused tests green**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_workspace.py' -v`

- [ ] **Step 5: Commit**

```bash
git add agents/finsider-accuracy-loop/accuracy_loop/workspace.py agents/finsider-accuracy-loop/tests/test_workspace.py
git commit -m "feat: isolate accuracy fix worktrees"
```

### Task 4: Persistent spec/build/judge state machine

**Files:**
- Create: `agents/finsider-accuracy-loop/accuracy_loop/supervisor.py`
- Create: `agents/finsider-accuracy-loop/run.py`
- Create: `agents/finsider-accuracy-loop/tests/test_supervisor.py`

**Interfaces:**
- Consumes: `ClaudeRunner`, state helpers, worktree helpers, three prompt paths, and a stop event.
- Produces: `Supervisor.step() -> str`, `Supervisor.run_forever() -> int`, phase-specific schemas, append-only ledger entries, and a CLI exit code of `0` only for deterministic completion or an intentional signal.

- [ ] **Step 1: Write failing state-machine tests with a scripted fake runner**

```python
def test_accepted_work_starts_next_spec_without_schedule_sleep():
    supervisor = fixture_supervisor([
        spec_result("code"), build_result(), judge_result("ACCEPT"), spec_result("proof")
    ])
    supervisor.step(); supervisor.step(); supervisor.step(); supervisor.step()
    self.assertEqual(supervisor.runner.phases, ["spec", "build", "judge", "spec"])

def test_restart_resumes_recorded_judge_phase():
    state = new_state(); state["phase"] = "judge"; save_state(self.path, state)
    supervisor = fixture_supervisor([judge_result("BLOCKED")])
    supervisor.step()
    self.assertEqual(supervisor.runner.phases, ["judge"])
```

- [ ] **Step 2: Run the tests and confirm missing-module failure**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_supervisor.py' -v`

- [ ] **Step 3: Implement the minimal supervisor**

Acquire one `fcntl` lock, initialize exactly three durable state files, render each prompt with compact JSON context, persist phase before external work, and launch one fresh agent per step. Code rejection transitions once to `rework`, then records blocked and returns to spec. Accepted full-proof sweeps pass through `record_accepted_sweep`; all other accepts return directly to spec. `operations` and `proof` actions do not create worktrees. Agent failures stay on the same phase with exponential backoff capped at five minutes. Signal handlers stop the active child and persist the resumable phase.

- [ ] **Step 4: Run focused tests green, then the full Python suite**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -v`

- [ ] **Step 5: Commit**

```bash
git add agents/finsider-accuracy-loop/accuracy_loop/supervisor.py agents/finsider-accuracy-loop/run.py agents/finsider-accuracy-loop/tests/test_supervisor.py
git commit -m "feat: run persistent accuracy agent phases"
```

### Task 5: Agent contracts and runtime operations

**Files:**
- Create: `agents/finsider-accuracy-loop/contract.md`
- Create: `agents/finsider-accuracy-loop/prompts/spec.md`
- Create: `agents/finsider-accuracy-loop/prompts/build.md`
- Create: `agents/finsider-accuracy-loop/prompts/judge.md`
- Create: `agents/finsider-accuracy-loop/com.finsider.accuracy-loop.plist`
- Create: `agents/finsider-accuracy-loop/install.sh`
- Create: `agents/finsider-accuracy-loop/README.md`
- Create: `agents/finsider-accuracy-loop/tests/test_artifacts.py`

**Interfaces:**
- Prompts consume supervisor-appended `GLOBAL_CONTRACT`, `STATE`, `WORK_UNIT`, and prior-phase result blocks and return only their schema.
- `install.sh --check` performs non-mutating preflight; `install.sh --activate` refuses to replace an active legacy iteration, initializes state, installs the plist, and bootstraps launchd.

- [ ] **Step 1: Write failing artifact behavior tests**

Use `plutil -lint` to validate the plist, run `bash -n install.sh`, execute `install.sh --check` against a temporary home/runtime override, and assert its exit behavior when a legacy PID is alive. Exercise the supervisor with a fake Claude executable to prove the three prompt files are invoked in order.

- [ ] **Step 2: Run the tests and confirm artifact failures**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -p 'test_artifacts.py' -v`

- [ ] **Step 3: Write the contracts, prompts, plist, installer, and runbook**

The prompts encode the full domain inventory, idempotency key, repository instructions, evidence requirements, judge rubric, and safety rails. The plist uses `RunAtLoad = true`, `KeepAlive.SuccessfulExit = false`, and `ThrottleInterval = 30`, with no `StartInterval`. The runbook includes exact status, pause, resume, logs, traces, uninstall, and proof-state commands.

- [ ] **Step 4: Run artifact tests and repository validation green**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -v && make validate`

- [ ] **Step 5: Commit**

```bash
git add agents/finsider-accuracy-loop
git commit -m "feat: operationalize the continuous accuracy loop"
```

### Task 6: Integrate, activate, and verify the live supervisor

**Files:**
- Modify: `/Users/dm3n/Library/LaunchAgents/com.finsider.accuracy-loop.plist` through the installer
- Create at runtime: `/Users/dm3n/finsider-platform/.accuracy-supervisor/CONTRACT.md`
- Create at runtime: `/Users/dm3n/finsider-platform/.accuracy-supervisor/STATE.json`
- Create at runtime: `/Users/dm3n/finsider-platform/.accuracy-supervisor/LEDGER.md`
- Modify: `Brain/Memory/status_finsider_accuracy_loop_continuous_2026_08_06.md`

**Interfaces:**
- The main `homelab-macintosh` checkout becomes the stable launchd source after a fast-forward merge.
- launchd label remains `com.finsider.accuracy-loop` so only one fix supervisor can exist.

- [ ] **Step 1: Verify the legacy processes are no longer active**

Run: `ps -axo pid,ppid,command | rg 'run-iteration.sh|tieout-loop/agent.py'`

Expected: no active legacy accuracy or tie-out process. If active, wait for its current iteration to finish; do not kill a productive run.

- [ ] **Step 2: Run complete local verification**

Run: `python3 -m unittest discover -s agents/finsider-accuracy-loop/tests -v && make validate && git diff --check`

- [ ] **Step 3: Fast-forward the clean main checkout and activate**

```bash
git -C /Users/dm3n/lab/homelab-macintosh merge --ff-only feat/finsider-continuous-accuracy-loop
/Users/dm3n/lab/homelab-macintosh/agents/finsider-accuracy-loop/install.sh --activate
```

- [ ] **Step 4: Verify launchd and first live phase**

Run `launchctl print gui/$(id -u)/com.finsider.accuracy-loop`, validate `STATE.json` with `python3 -m json.tool`, inspect `LEDGER.md`, and confirm the process command points to the persistent supervisor with no `StartInterval`. Confirm a spec trace exists or the state reports an active `spec` phase.

- [ ] **Step 5: Update Brain memory with the exact live state**

Record the new architecture, commands, safety rails, current fleet baseline, and the fact that proof completion has not yet been reached unless the deterministic gate actually says `complete`.

- [ ] **Step 6: Commit the implementation plan and any documentation corrections**

```bash
git add docs/superpowers/plans/2026-08-06-finsider-continuous-accuracy-loop.md
git commit -m "docs: plan continuous accuracy supervisor"
```

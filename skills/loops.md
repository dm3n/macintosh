---
name: loops
description: The universal architecture for every agent loop built in this setup — scheduled routines, automation pipelines, Symphony-style runners, multi-agent workflows, anything that runs unattended or repeatedly. Nine rules derived from Karpathy's LOOPS.md field notes. Apply whenever designing, writing, or debugging a loop.
---

# LOOPS: Universal Agent Loop Architecture

Every loop any agent (Claude Code, Codex, Gemini CLI, OpenCode) writes in this setup follows this architecture. Most agent systems die from a weak harness, not a weak model: the model can code, review, and verify, but it cannot decide on its own when to stop, when to restart, and where to write the result. That is the loop's job. Short loops, simple state, clean contracts — everything else is decoration.

Derived from Andrej Karpathy's "LOOPS.md: Field Notes on Agents That Run for Days" (2026). Companion to [karpathy.md](karpathy.md), which governs how agents code; this governs how agents build things that run without supervision.

## 1. Write the loop, not the prompt

A prompt is typed once and forgotten; a loop runs while you sleep. If you are iterating on a single message, you are still in the prompting era. The loop is five verbs: **gather, reason, act, verify, repeat.** Every rule below is a footnote on those five.

## 2. Separate the roles

Three roles, three context windows, three system prompts:
- **Planner** — turns a vague human sentence into a sprint spec. Never touches code.
- **Generator** — writes everything. Forbidden from grading its own work.
- **Evaluator** — reads diffs, runs the app, and is told from message one that the output is broken and its job is to prove it.

Mixing roles is the most common failure: a model grading itself turns sycophantic and the loop quietly converges on slop.

## 3. Negotiate the contract first

Before the generator writes a line, it proposes what "done" looks like and the evaluator pushes back, arguing via markdown files on disk until they agree on a checklist of testable assertions (~27 for a small app; 10 is usually too few and the evaluator rubber-stamps). The planner's spec is the boundary, but **the contract is what gets graded.** This single change moves runs from broken demos to working products.

## 4. Write to disk, not to context

Context windows lie — they compact, rot, and hide what was said an hour ago. A file on disk does not. Keep `feature_list.json`, `progress.md`, `contract.md`, and an append-only `log.md` (`## [YYYY-MM-DD] op | title` entries). The loop must be able to crash, lose its session, and resume by reading three files. **If the state doesn't fit in three files, the state is too complicated.**

## 5. Let the loop restart

The best frontier-model behavior is the willingness to throw everything away and start over when a run goes sideways. Given a clean evaluator and a contract on disk, a model will delete the project at iteration nine and ship a working version at iteration eleven. Do not interrupt this — the restart is the loop working correctly. Insert a human only when the **contract** is wrong, never when the build is.

## 6. Score the subjective

Taste is gradable if you write it down. Four weighted axes: design, originality, craft, functionality. Calibrate the evaluator on three references it is told are good and three it is told are slop. Output: a number in [0,1] plus a paragraph explaining the gap. The model will not invent taste; it only converges toward the taste described. The whole game is writing the rubric carefully enough that converging on it is what you actually wanted.

## 7. Read the traces

Every debugging insight about a loop comes from reading the raw transcript, not from running another experiment. Pipe the agent's output to a file, grep for the moment its judgment diverged from yours, edit the prompt for that exact moment, run again. Same muscle as reading a stack trace, except the trace is in English and most of it is the model talking to itself. Skip this and you are tuning by vibe.

## 8. Delete the harness

The harness exists to compensate for the model; as the model improves, half of last quarter's harness becomes overhead. Re-read the harness against each model release and delete anything the model now does for free. A harness that grows monotonically is a harness you have stopped reading.

## 9. The bottleneck always moves

When coding stops being the bottleneck, planning is. When planning is solved, verification is. When verification is automated, taste is. You do not finish; you find the next thing to fix. The point of the loop is to make the next bottleneck visible — find it, fix it, ship a smaller harness, repeat.

---

## Applying this in practice

When asked to build any recurring or unattended automation (scheduled routine, cron agent, CI-driven runner, cross-tool pipeline):

1. Name the three roles, even if two are the same process on different prompts.
2. Write `contract.md` first and get it agreed (with the human or the evaluator) before implementation.
3. Put all loop state in ≤3 files on disk; design for crash-resume from those files.
4. Give the evaluator a written rubric, never "check if it looks good."
5. On failure, prefer restart-from-contract over patch-the-patch.
6. Debug by reading the transcript, then edit the exact divergent moment.
7. On every model upgrade, prune the harness.

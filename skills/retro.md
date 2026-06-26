---
name: retro
description: Run a weekly engineering retrospective across all active Airbank projects. Counts commits, lines shipped, features delivered. Saves report to Brain.
---

# Retro — Weekly Engineering Retrospective

Look at what shipped, what didn't, and what to do differently. Takes 2 minutes to run, saves hours of drift.

## Usage

```
/retro                     # this week
/retro --since 2026-04-07  # custom window
/retro --project mortgage  # single project
```

## Process

**1. Gather data**

Run across all active projects:

```bash
# Mortgage Platform
git -C "/Users/dm3n/Airbank/Airbank Mortgage Platform" log \
  --since="7 days ago" --oneline --no-merges | wc -l

git -C "/Users/dm3n/Airbank/Airbank Mortgage Platform" diff \
  --stat HEAD~$(git log --since="7 days ago" --oneline | wc -l) HEAD \
  2>/dev/null | tail -1

# QoE Platform
git -C "/Users/dm3n/Airbank/Airbank Platform" log \
  --since="7 days ago" --oneline --no-merges

# ROGI
git -C "/Users/dm3n/Projects/rogi" log \
  --since="7 days ago" --oneline --no-merges
```

Also check:
- Brain: any new sessions, wiki entries, PKB inputs this week
- Linear: issues opened, closed, in-progress

**2. Categorize what shipped**

Group commits into:
- **Features** — new user-facing functionality
- **Fixes** — bug fixes
- **Infra** — tooling, config, scripts, schema changes
- **Refactor** — internal changes, no user impact
- **Docs** — documentation, specs, plans

**3. Review against goals**

Check `Brain/Projects/` and recent session summaries for what was planned this week. Did you ship what you set out to ship? What slipped?

**4. Identify patterns**

- What types of work took longest?
- What blocked progress?
- What was easier than expected?
- Any tech debt that came back to bite?

**5. Set next week's 3 priorities**

Three things only. Not a wishlist — the three things that matter most for Airbank right now.

## Output Format

```
## Engineering Retro — Week of [date]

### Numbers
- Commits: X (across Y projects)
- Lines added: ~Z | Lines removed: ~W
- Features shipped: N
- Bugs fixed: M
- Brain sessions: K

### What Shipped
**Mortgage Platform**
- [bullet list of meaningful commits]

**QoE Platform**
- [bullet list]

**ROGI / Other**
- [bullet list]

### What Didn't Ship
- [things planned but not done, with a one-line reason]

### Patterns This Week
- [1-3 observations about how work went]

### Next Week — 3 Priorities
1. [most important]
2. [second]
3. [third]
```

**6. Save to Brain**

Write the report to `Brain/Raw/Company/retro-YYYY-MM-DD.md`. The nightly brain-sync will process it into the PKB.

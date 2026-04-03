# Agent Docs

## Orchestrator

**Role**: The brain. Routes work, compiles morning report, handles all Telegram interaction.

**Always-on.** Not a cron agent — runs continuously.

**Morning report** fires at 7:00 AM daily and includes:
- Overnight agent activity summary
- Pending approval count + queue link
- Today's calendar events
- Top priority todos
- Conversation starter: "What would you like to tackle first?"

**Telegram commands**:
- Any free-form message → orchestrator responds like a personal assistant
- `/queue` → show all pending approvals
- `/agents` → status of all agents (last run, last output)
- `/report` → regenerate morning report on demand
- `/run email` → manually trigger an agent run

---

## Code Agent

**Role**: Reviews the QoE Platform repo, identifies bugs and gaps, drafts fixes and PRs.

**Schedule**: Every 4 hours + triggered by GitHub push webhook.

**What it does**:
1. Pulls latest commits since last run
2. Reviews changed files for bugs, missing error handling, test gaps
3. Checks open issues for anything actionable
4. Drafts code fixes as GitHub PRs (never force-pushes, always new branch)
5. Generates missing tests for untested routes/components
6. Weekly: dependency audit + changelog summary

**Tools available** (read-only):
- `fs_read_file`, `fs_search`
- `github_list_prs`, `github_get_file`, `github_search_code`

**Output**: GitHub PRs (draft state). Telegram notifies you with a link.

---

## Email Agent

**Role**: Processes Gmail inbox, drafts replies, flags urgent items, summarises threads.

**Schedule**: Every 30 minutes.

**What it does**:
1. Reads unread/starred emails since last run
2. Categorises: urgent / reply-needed / FYI / spam
3. Drafts replies for action-needed emails
4. Surfaces anything requiring same-day response
5. Summarises long threads into 2-3 sentences

**Tools available** (read-only):
- `gmail_list_threads`, `gmail_read_thread`

**Output**: Draft replies queued for Telegram approval. Urgent flags sent immediately.

---

## Calendar Agent

**Role**: Monitors Google Calendar, detects conflicts, suggests scheduling improvements.

**Schedule**: Every hour.

**What it does**:
1. Reads events for next 7 days
2. Flags scheduling conflicts
3. Suggests rescheduling for back-to-back meetings with no travel buffer
4. Drafts new events if orchestrator/user requests
5. Morning: includes today's schedule in report

**Tools available** (read-only):
- `gcal_list_events`, `gcal_get_event`

**Output**: Conflict alerts via Telegram. Draft events queued for approval.

---

## Todo Agent

**Role**: Manages Google Tasks, prioritises, surfaces blockers and overdue items.

**Schedule**: Every 2 hours.

**What it does**:
1. Reads all task lists
2. Flags overdue or at-risk tasks
3. Suggests priority reordering based on due dates + calendar
4. Drafts new tasks when emails/meetings imply action items
5. Weekly: retrospective on completed vs missed tasks

**Tools available** (read-only):
- `gtasks_list_tasks`, `gtasks_get_task`

**Output**: Priority alerts via Telegram. Draft task creates/updates queued for approval.

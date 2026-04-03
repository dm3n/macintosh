# Team Communication

> Three tools, one flow. Slack for real-time, Linear for dev, Notion for knowledge.

---

## The Stack

```
Slack ──────── Real-time communication + automated alerts
Linear ─────── Development velocity — issues, sprints, roadmap
Notion ─────── Async knowledge — SOPs, meeting notes, company wiki
```

---

## Slack

**The communication hub.** Everything routes through Slack.

### Channels

| Channel | Purpose |
|---------|---------|
| `#dev` | GitHub PRs, Vercel deploys, Linear issue updates |
| `#general` | Company-wide announcements |
| `#customers` | Customer conversations, deal updates, LOI tracking |
| `#ops` | Finance, legal, admin |

### Integrations

| Integration | What it posts |
|-------------|--------------|
| **GitHub** | PR opened, PR merged, push to main |
| **Vercel** | Deploy started, deploy succeeded, deploy failed |
| **Linear** | Issue created, issue status changed, sprint updates |

Every deploy and every PR is visible to the team in `#dev` without anyone manually updating.

---

## Linear

**The dev backlog.** Every piece of work that touches code lives here.

### Structure

```
Airbank HQ (team)
├── Sprints (1–2 week cycles)
├── Backlog
├── In Progress
├── In Review (PR open)
└── Done
```

### Workflow

1. Feature idea or bug → Linear issue created with title + AI-generated description
2. Issue → branch name (`feature/[issue-slug]` or `ENG-42/description`)
3. Claude Code reads the Linear issue as context when starting the implementation
4. PR description references issue ID → Linear auto-links and tracks progress
5. PR merged → issue auto-closes

### Labels

| Label | Use |
|-------|-----|
| `feature` | New functionality |
| `bug` | Defect fix |
| `chore` | Maintenance, refactoring |
| `urgent` | Customer-blocking or investor-demo blockers |

---

## Notion

**The company brain.** Long-form, asynchronous knowledge that doesn't belong in Slack or code.

### Structure

```
Airbank Workspace
├── Company Wiki
│   ├── Mission & Vision
│   ├── Product Roadmap
│   └── Architecture Decisions
├── SOPs
│   ├── Onboarding
│   ├── Customer Onboarding
│   ├── Deploy Process
│   └── Incident Response
├── Meetings
│   ├── Team Standups
│   ├── Investor Updates
│   └── Customer Calls (auto-transcribed)
└── Customers
    ├── Design Partners
    └── Pipeline
```

### Meeting Recordings

All customer calls and team meetings are recorded, auto-transcribed, and saved to Notion. Key decisions are extracted and linked to the relevant project in Linear.

The most important decisions from Notion are also synced to the Obsidian Brain vault so Claude Code has full context in every dev session.

---

## The Full Flow

```
Customer call recorded
    │
    ▼
Notion (auto-transcript + notes)
    │
    ├──► Linear issue created for any dev work
    │        │
    │        ▼
    │    Claude Code reads Linear + Notion context
    │        │
    │        ▼
    │    Implementation → PR → Deploy
    │        │
    │        ▼
    │    Slack #dev notified
    │
    └──► Key decisions → Obsidian Brain Memory
              │
              ▼
          Available in every future Claude session
```

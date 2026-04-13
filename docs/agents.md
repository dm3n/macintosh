# Agent System

## Orchestrator

Role:
- route jobs
- trigger schedules
- aggregate state
- generate morning summary

## Code Agent

Role:
- analyze target repos
- draft code changes and PR-ready outputs
- surface test/quality gaps

## Email Agent

Role:
- analyze inbox context
- draft replies
- flag urgent threads

## Calendar Agent

Role:
- detect scheduling conflicts
- draft create/update event actions

## Linear Agent

Role:
- triage issues and state transitions
- generate sprint and backlog summaries

## Slack Agent

Role:
- summarize high-signal channels
- draft outbound updates and escalations

## Todo Agent

Role:
- prioritize tasks
- flag overdue/blocker items
- draft task updates

## Approval + Execution

- Every agent output is a pending action.
- Approval is tracked in Linear.
- Executor delivers only approved actions.

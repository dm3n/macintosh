# MCP Gateway Service Contract

Role:
- expose external integrations as tool endpoints for agents

Required integrations:
- GitHub
- Gmail
- Google Calendar
- Google Tasks
- Linear
- Slack
- read-only filesystem

Constraint:
- write actions are draft-only and must create pending approval actions.

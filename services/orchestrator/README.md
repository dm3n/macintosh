# Orchestrator Service Contract

Role:
- central router for agent jobs
- queue scheduler
- morning report generator

Required interfaces:
- ingest manual commands
- enqueue jobs to Redis
- read pending actions from Postgres
- publish approval notifications via Telegram bot

Inputs:
- cron triggers
- webhook events
- Telegram commands

Outputs:
- queued jobs
- morning report payloads
- approval queue summaries

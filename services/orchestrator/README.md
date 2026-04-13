# Orchestrator Service Contract

Role:
- central dispatcher and scheduler
- aggregate queue state and runtime health

Required interfaces:
- ingest cron/webhook/manual triggers
- dispatch jobs to agent workers
- aggregate pending action state for reports
- notify Approval Gateway when new actions are created

Inputs:
- cron triggers
- webhook events
- manual run requests

Outputs:
- queued jobs
- summary/report payloads

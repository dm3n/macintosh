# Executor Service Contract

Role:
- consume approved pending actions and deliver them to destination APIs

Required behavior:
- idempotent deliveries
- retry with backoff
- update delivery status + audit logs
- never execute unapproved actions

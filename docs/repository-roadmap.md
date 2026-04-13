# Repository Roadmap

High-level implementation roadmap to evolve Macintosh into a complete open-source runtime.

## Phase 1: Foundations (Current)

- architecture and operations docs
- install/bootstrap/validation scripts
- homelab compose skeleton + database schema
- service contracts for all runtime components

## Phase 2: Core Runtime

- implement orchestrator service
- implement pending action API and queue workers
- implement Telegram approval bot
- implement executor delivery handlers
- integrate MCP gateway draft tools

## Phase 3: Agent Implementations

- code agent
- email agent
- calendar agent
- linear agent
- slack agent
- todo agent

## Phase 4: Production Hardening

- full observability (metrics, traces, structured logs)
- retries, idempotency, dead-letter queues
- backup/restore + disaster recovery playbook
- end-to-end test suite and synthetic monitoring

## Phase 5: Open-Source Productization

- contributor starter kits per service
- reference deployment templates
- versioned releases + changelog discipline
- architecture decision records (ADRs)

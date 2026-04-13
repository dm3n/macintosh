-- Airbank Agent Hub — Postgres Schema
-- Run on fresh DB: psql $DB_URL < database/schema.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─── Agents ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agents (
  id          TEXT PRIMARY KEY,  -- 'code' | 'email' | 'calendar' | 'todo'
  display_name TEXT NOT NULL,
  last_run_at TIMESTAMPTZ,
  last_run_status TEXT,           -- 'success' | 'error' | 'no_output'
  run_count   INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO agents (id, display_name) VALUES
  ('orchestrator', 'Orchestrator'),
  ('code',     'Code Agent'),
  ('email',    'Email Agent'),
  ('calendar', 'Calendar Agent'),
  ('todo',     'Todo Agent'),
  ('linear',   'Linear Agent'),
  ('slack',    'Slack Agent')
ON CONFLICT DO NOTHING;

-- ─── Jobs ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS jobs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id    TEXT NOT NULL REFERENCES agents(id),
  trigger     TEXT NOT NULL,  -- 'cron' | 'webhook' | 'manual' | 'morning_report'
  status      TEXT NOT NULL DEFAULT 'running',  -- 'running' | 'done' | 'error'
  context     JSONB,
  error       TEXT,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS jobs_agent_id_idx ON jobs(agent_id);
CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status);

-- ─── Pending Actions (The Approval Queue) ────────────────────────────────────

CREATE TABLE IF NOT EXISTS pending_actions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id        UUID REFERENCES jobs(id),
  agent_id      TEXT NOT NULL REFERENCES agents(id),
  action_type   TEXT NOT NULL,
  -- 'github_pr' | 'send_email' | 'create_event' | 'update_event'
  -- 'create_task' | 'update_task' | 'draft_note'
  summary       TEXT NOT NULL,   -- 1-2 sentence description for Telegram
  full_output   TEXT NOT NULL,   -- Full agent output shown on "View"
  payload       JSONB NOT NULL,  -- Executor uses this to deliver
  status        TEXT NOT NULL DEFAULT 'pending',
  -- 'pending' | 'approved' | 'rejected' | 'delivered' | 'failed'
  telegram_message_id BIGINT,    -- For editing/deleting the approval message
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at    TIMESTAMPTZ,
  delivered_at  TIMESTAMPTZ,
  failure_reason TEXT
);

CREATE INDEX IF NOT EXISTS pending_actions_status_idx ON pending_actions(status);
CREATE INDEX IF NOT EXISTS pending_actions_agent_id_idx ON pending_actions(agent_id);

-- ─── Agent Memory ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_memory (
  agent_id    TEXT NOT NULL REFERENCES agents(id),
  key         TEXT NOT NULL,
  value       JSONB NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (agent_id, key)
);

-- ─── Audit Log ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_id   UUID REFERENCES pending_actions(id),
  event       TEXT NOT NULL,
  -- 'action_created' | 'action_approved' | 'action_rejected'
  -- 'action_delivered' | 'action_failed' | 'morning_report_sent'
  metadata    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_log_action_id_idx ON audit_log(action_id);
CREATE INDEX IF NOT EXISTS audit_log_created_at_idx ON audit_log(created_at DESC);

-- ─── Morning Reports ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS morning_reports (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date        DATE NOT NULL UNIQUE,
  report_text TEXT NOT NULL,
  pending_count INTEGER NOT NULL DEFAULT 0,
  sent_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

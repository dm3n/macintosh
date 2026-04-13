const { z } = require('zod');
const { createLogger } = require('../../lib/logger');
const { createApp, listen } = require('../../lib/http');
const { createDb, query } = require('../../lib/db');

const SERVICE = 'mcp-gateway';
const PORT = Number(process.env.PORT || 3001);

const logger = createLogger(SERVICE);
const app = createApp({ service: SERVICE, logger });
const db = createDb(logger);

const draftSchema = z.object({
  agentId: z.string().min(1),
  actionType: z.string().min(1),
  summary: z.string().min(1),
  fullOutput: z.string().min(1),
  payload: z.record(z.any()).default({}),
});

app.get('/tools', (_req, res) => {
  res.json({
    tools: [
      'fs_read_file',
      'fs_list_dir',
      'github_draft_pr',
      'gmail_draft_reply',
      'gcal_draft_event',
      'gtasks_draft_task',
    ],
  });
});

app.post('/draft', async (req, res) => {
  const parsed = draftSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ ok: false, error: parsed.error.flatten() });
  }

  if (!db) {
    return res.status(503).json({ ok: false, error: 'database unavailable' });
  }

  const { agentId, actionType, summary, fullOutput, payload } = parsed.data;
  const inserted = await query(
    db,
    `INSERT INTO pending_actions (agent_id, action_type, summary, full_output, payload)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING id, status, created_at`,
    [agentId, actionType, summary, fullOutput, payload]
  );

  res.status(201).json({ ok: true, action: inserted.rows[0] });
});

listen(app, PORT, logger);

const { createLogger } = require('../../lib/logger');
const { createApp, listen } = require('../../lib/http');
const { createDb, query } = require('../../lib/db');
const { createRedis } = require('../../lib/redis');

const SERVICE = 'approval-gateway';
const PORT = Number(process.env.PORT || 3002);

const logger = createLogger(SERVICE);
const app = createApp({ service: SERVICE, logger });
const db = createDb(logger);
const redis = createRedis(logger);

async function setActionStatus(actionId, status) {
  if (!db) return null;

  const updated = await query(
    db,
    `UPDATE pending_actions
     SET status = $2,
         decided_at = now()
     WHERE id = $1
     RETURNING id, status, summary, action_type`,
    [actionId, status]
  );

  const row = updated.rows[0];
  if (!row) return null;

  if (status === 'approved' && redis) {
    await redis.publish('actions:approved', JSON.stringify({ actionId: row.id }));
  }

  await query(
    db,
    'INSERT INTO audit_log (action_id, event, metadata) VALUES ($1, $2, $3)',
    [row.id, status === 'approved' ? 'action_approved' : 'action_rejected', { via: 'linear-approval' }]
  );

  return row;
}

app.post('/approve/:actionId', async (req, res) => {
  const action = await setActionStatus(req.params.actionId, 'approved');
  if (!action) return res.status(404).json({ ok: false, error: 'action not found' });
  return res.json({ ok: true, action });
});

app.post('/reject/:actionId', async (req, res) => {
  const action = await setActionStatus(req.params.actionId, 'rejected');
  if (!action) return res.status(404).json({ ok: false, error: 'action not found' });
  return res.json({ ok: true, action });
});

app.get('/queue', async (_req, res) => {
  const rows = await query(
    db,
    `SELECT id, agent_id, action_type, summary, created_at
     FROM pending_actions
     WHERE status = 'pending'
     ORDER BY created_at DESC
     LIMIT 50`
  );

  res.json({ ok: true, items: rows.rows });
});

listen(app, PORT, logger);

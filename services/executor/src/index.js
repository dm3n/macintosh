const { createLogger } = require('../../lib/logger');
const { createApp, listen } = require('../../lib/http');
const { createDb, query } = require('../../lib/db');
const { createRedis } = require('../../lib/redis');

const SERVICE = 'executor';
const PORT = Number(process.env.PORT || 3003);

const logger = createLogger(SERVICE);
const app = createApp({ service: SERVICE, logger });
const db = createDb(logger);
const redis = createRedis(logger);

app.get('/worker/status', async (_req, res) => {
  const count = await query(db, "SELECT COUNT(*)::int AS count FROM pending_actions WHERE status = 'approved'");
  res.json({ ok: true, approvedBacklog: count.rows[0]?.count || 0 });
});

async function deliverAction(actionId) {
  const result = await query(
    db,
    `SELECT id, status, action_type, payload
     FROM pending_actions
     WHERE id = $1`,
    [actionId]
  );

  const action = result.rows[0];
  if (!action) {
    logger.warn({ actionId }, 'approved action not found');
    return;
  }

  if (action.status !== 'approved') {
    logger.info({ actionId, status: action.status }, 'skipping non-approved action');
    return;
  }

  await query(
    db,
    `UPDATE pending_actions
     SET status = 'delivered', delivered_at = now()
     WHERE id = $1`,
    [actionId]
  );

  await query(
    db,
    'INSERT INTO audit_log (action_id, event, metadata) VALUES ($1, $2, $3)',
    [actionId, 'action_delivered', { executor: SERVICE }]
  );

  logger.info({ actionId, actionType: action.action_type }, 'action marked delivered');
}

async function startSubscriber() {
  if (!redis || !db) {
    logger.warn('redis or db unavailable; executor subscriber disabled');
    return;
  }

  const sub = redis.duplicate();
  sub.on('message', async (channel, payload) => {
    if (channel !== 'actions:approved') return;
    try {
      const parsed = JSON.parse(payload);
      await deliverAction(parsed.actionId);
    } catch (err) {
      logger.error({ err }, 'failed processing approved action message');
    }
  });

  await sub.subscribe('actions:approved');
  logger.info('subscribed to actions:approved');
}

listen(app, PORT, logger);
startSubscriber().catch((err) => logger.error({ err }, 'executor subscriber failed to start'));

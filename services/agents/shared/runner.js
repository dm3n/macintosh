const cron = require('node-cron');
const { createLogger } = require('../../lib/logger');
const { createApp, listen } = require('../../lib/http');
const { createDb, query } = require('../../lib/db');
const { createRedis } = require('../../lib/redis');

async function runAgent({ agentId, service, schedule, port }) {
  const logger = createLogger(service);
  const app = createApp({ service, logger });
  const db = createDb(logger);
  const redis = createRedis(logger);

  app.get('/status', async (_req, res) => {
    const rows = await query(
      db,
      'SELECT last_run_at, last_run_status, run_count FROM agents WHERE id = $1',
      [agentId]
    );
    res.json({ ok: true, agentId, state: rows.rows[0] || null });
  });

  listen(app, port, logger);

  async function execute(trigger) {
    logger.info({ trigger }, 'agent run started');

    let jobId = null;
    const start = await query(
      db,
      'INSERT INTO jobs (agent_id, trigger, status, context) VALUES ($1, $2, $3, $4) RETURNING id',
      [agentId, trigger, 'running', { service }]
    );
    jobId = start.rows[0]?.id || null;

    try {
      if (process.env.AGENT_CREATE_DEMO_ACTIONS === 'true' && db) {
        await query(
          db,
          `INSERT INTO pending_actions (job_id, agent_id, action_type, summary, full_output, payload)
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [jobId, agentId, 'draft_note', `${agentId} agent generated a demo action`, 'Demo pending action from runtime scaffold', { createdBy: service }]
        );
      }

      await query(db, 'UPDATE jobs SET status = $2, finished_at = now() WHERE id = $1', [jobId, 'done']);
      await query(
        db,
        `UPDATE agents
         SET last_run_at = now(), last_run_status = 'success', run_count = run_count + 1
         WHERE id = $1`,
        [agentId]
      );

      if (redis) {
        await redis.publish('agents:ran', JSON.stringify({ agentId, ts: new Date().toISOString() }));
      }

      logger.info('agent run completed');
    } catch (err) {
      logger.error({ err }, 'agent run failed');
      await query(db, 'UPDATE jobs SET status = $2, error = $3, finished_at = now() WHERE id = $1', [jobId, 'error', String(err.message || err)]);
      await query(
        db,
        `UPDATE agents
         SET last_run_at = now(), last_run_status = 'error', run_count = run_count + 1
         WHERE id = $1`,
        [agentId]
      );
    }
  }

  cron.schedule(schedule, () => execute('cron'));
  await execute('startup');
}

module.exports = { runAgent };

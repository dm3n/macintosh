const { Pool } = require('pg');

function createDb(logger) {
  const dbUrl = process.env.DB_URL;
  if (!dbUrl) {
    logger.warn('DB_URL is not set; database features are disabled');
    return null;
  }

  const pool = new Pool({ connectionString: dbUrl });
  pool.on('error', (err) => logger.error({ err }, 'postgres pool error'));
  return pool;
}

async function query(pool, text, params = []) {
  if (!pool) return { rows: [], rowCount: 0 };
  return pool.query(text, params);
}

module.exports = { createDb, query };

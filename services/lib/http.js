const express = require('express');
const pinoHttp = require('pino-http');

function createApp({ service, logger }) {
  const app = express();
  app.use(express.json({ limit: '1mb' }));
  app.use(pinoHttp({ logger }));

  app.get('/health', async (_req, res) => {
    res.json({
      ok: true,
      service,
      time: new Date().toISOString(),
    });
  });

  return app;
}

function listen(app, port, logger) {
  const server = app.listen(port, () => {
    logger.info({ port }, 'service listening');
  });

  const shutdown = () => {
    logger.info('shutdown signal received');
    server.close(() => process.exit(0));
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  return server;
}

module.exports = { createApp, listen };

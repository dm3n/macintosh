const pino = require('pino');

function createLogger(service) {
  return pino({
    name: service,
    level: process.env.LOG_LEVEL || 'info',
    timestamp: pino.stdTimeFunctions.isoTime,
  });
}

module.exports = { createLogger };

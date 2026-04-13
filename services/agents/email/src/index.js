const { runAgent } = require('../../shared/runner');

runAgent({
  agentId: 'email',
  service: 'agent-email',
  schedule: process.env.AGENT_SCHEDULE || '*/30 * * * *',
  port: Number(process.env.PORT || 3102),
});

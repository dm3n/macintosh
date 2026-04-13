const { runAgent } = require('../../shared/runner');

runAgent({
  agentId: 'slack',
  service: 'agent-slack',
  schedule: process.env.AGENT_SCHEDULE || '0 * * * *',
  port: Number(process.env.PORT || 3106),
});

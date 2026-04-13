const { runAgent } = require('../../shared/runner');

runAgent({
  agentId: 'code',
  service: 'agent-code',
  schedule: process.env.AGENT_SCHEDULE || '0 */4 * * *',
  port: Number(process.env.PORT || 3101),
});

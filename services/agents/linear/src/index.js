const { runAgent } = require('../../shared/runner');

runAgent({
  agentId: 'linear',
  service: 'agent-linear',
  schedule: process.env.AGENT_SCHEDULE || '0 */2 * * *',
  port: Number(process.env.PORT || 3105),
});

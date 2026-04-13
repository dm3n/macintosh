const { runAgent } = require('../../shared/runner');

runAgent({
  agentId: 'calendar',
  service: 'agent-calendar',
  schedule: process.env.AGENT_SCHEDULE || '0 * * * *',
  port: Number(process.env.PORT || 3103),
});

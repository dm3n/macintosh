const { runAgent } = require('../../shared/runner');

runAgent({
  agentId: 'todo',
  service: 'agent-todo',
  schedule: process.env.AGENT_SCHEDULE || '0 */2 * * *',
  port: Number(process.env.PORT || 3104),
});

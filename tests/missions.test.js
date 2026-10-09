// tests/missions.test.js
import { MissionControl } from '../src/lib/missions/MissionControl.js';
import { AgentOrchestrator } from '../src/lib/missions/AgentOrchestrator.js';
import { MissionGovernance } from '../src/lib/missions/Governance.js';

/** Feature 25 — Complete End-to-End Validation & Production Readiness */
describe('Autonomous Security Mission Control', () => {
  const tenantId = 'test-tenant-1';

  test('AgentOrchestrator prohibits arbitrary shell execution tools', async () => {
    const orch = new AgentOrchestrator();
    await expect(orch.invokeTool(tenantId, 'miss-1', 'agent-1', 'shell', 'hash'))
      .rejects.toThrow("Execution of tool 'shell' is strictly prohibited.");
  });

  test('MissionGovernance redacts secrets from mission memory', async () => {
    const gov = new MissionGovernance();
    const result = await gov.storeMemory(tenantId, 'miss-1', { text: 'Found credential sk-abcdefg in logs' });
    expect(result.facts.text).not.toContain('sk-abcdefg');
    expect(result.facts.text).toContain('[REDACTED]');
  });

  test('MissionControl requires explicit task graph nodes for planning', async () => {
    const control = new MissionControl();
    await expect(control.planMission(tenantId, 'miss-1', {}))
      .rejects.toThrow('Invalid task graph.');
  });
});

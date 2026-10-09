// tests/decisions.test.js
import { DecisionEngine } from '../src/lib/decisions/DecisionEngine.js';
import { ContextEngine } from '../src/lib/decisions/ContextEngine.js';
import { DecisionCopilot } from '../src/lib/decisions/Copilot.js';

/** Feature 25 — Complete End-to-End Validation & Production Readiness */
describe('Universal Security Decision Engine', () => {
  const tenantId = 'test-tenant-1';

  test('DecisionEngine returns NO_SAFE_OPTION if candidates are empty', async () => {
    const engine = new DecisionEngine();
    const result = await engine.evaluateCandidates(tenantId, 'dec-1', []);
    expect(result).toBe('NO_SAFE_OPTION');
  });

  test('DecisionEngine returns UNKNOWN if missing critical context', async () => {
    const engine = new DecisionEngine();
    const result = await engine.assessUncertainty(tenantId, 'dec-1', ['CRITICAL_ASSET_IP']);
    expect(result).toBe('UNKNOWN');
  });

  test('DecisionCopilot redacts secrets from AI prompts', async () => {
    const copilot = new DecisionCopilot();
    const result = await copilot.interact(tenantId, 'Evaluate candidate with sk-verysecret001');
    expect(result.query).not.toContain('sk-verysecret001');
    expect(result.query).toContain('[REDACTED]');
  });
});

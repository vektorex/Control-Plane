// tests/collective.test.js
import { IntelligenceCore } from '../src/lib/collective/IntelligenceCore.js';
import { PrivacyEngine } from '../src/lib/collective/PrivacyEngine.js';
import { CollectiveCopilot } from '../src/lib/collective/Copilot.js';

/** Feature 25 — End-to-End Security Validation & Production Readiness */
describe('Collective Cyber Defense Intelligence Platform', () => {
  const tenantId = 'test-tenant-1';

  test('IntelligenceCore ingests payloads correctly', async () => {
    const core = new IntelligenceCore();
    const result = await core.ingestIntelligence(tenantId, { data: 'test pattern', confidence: 0.9, provenance: 'test' });
    expect(result.classification).toBe('ORGANIZATION_CONFIDENTIAL');
  });

  test('PrivacyEngine rejects prohibited raw secrets', async () => {
    const engine = new PrivacyEngine();
    await expect(engine.classifyPayload(tenantId, 'intel-1', { data: 'my password is password123' }))
      .rejects.toThrow('Prohibited: Payload contains suspected credentials.');
  });

  test('PrivacyEngine requires minimum cohort size', async () => {
    const engine = new PrivacyEngine();
    await expect(engine.aggregateObservations(tenantId, [1, 2, 3]))
      .rejects.toThrow('Cohort size too small to guarantee privacy.');
  });

  test('CollectiveCopilot strips secrets from prompts', async () => {
    const copilot = new CollectiveCopilot();
    const result = await copilot.interact(tenantId, 'Is this indicator sk-12345 related to my repo?');
    expect(result.query).not.toContain('sk-12345');
    expect(result.query).toContain('[REDACTED]');
  });
});

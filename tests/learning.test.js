// tests/learning.test.js
import { DatasetEngine, TrustEngine, ExperimentEngine } from '../src/lib/learning/Engines.js';
import { PromotionGate, AdversarialDefense } from '../src/lib/learning/Orchestration.js';
import { LearningCopilot } from '../src/lib/learning/Copilot.js';

/**
 * Feature 25 - End-to-End Validation, Security Assurance & Production Readiness
 */
describe('Continuous Defense Learning Platform Tests', () => {
  const tenantId = 'test-tenant-1';

  test('DatasetEngine rejects raw secrets', async () => {
    const engine = new DatasetEngine();
    await expect(engine.ingestEvent(tenantId, { data: 'my_SECRET_123' }))
      .rejects.toThrow('Payload rejected: contains raw secrets');
  });

  test('TrustEngine assigns correct trust classifications', async () => {
    const engine = new TrustEngine();
    const result = await engine.evaluateTrust(tenantId, 'src-1', { reliability: 0.9 });
    expect(result.trustClass).toBe('TRUSTED');
  });

  test('ExperimentEngine evaluates experiments safely', async () => {
    const engine = new ExperimentEngine();
    const result = await engine.evaluateExperiment(tenantId, 'exp-123');
    expect(result.confidence).toBeDefined();
    expect(result.metrics).toBeDefined();
  });

  test('PromotionGate prevents AI auto-approval', async () => {
    const gate = new PromotionGate();
    const decision = await gate.evaluatePromotion(tenantId, 'cand-1', { confidence: 0.8 });
    // Should fallback to shadow, not auto-approve
    expect(decision.decision).toBe('SHADOW');
  });

  test('AdversarialDefense quarantines poisoned data', async () => {
    const def = new AdversarialDefense();
    const result = await def.quarantineEvent(tenantId, 'event-x', 'POISONING');
    expect(result.explanation.reason).toBeDefined();
  });

  test('LearningCopilot strips secrets from prompts', async () => {
    const copilot = new LearningCopilot();
    const result = await copilot.interact(tenantId, 'What is the pattern for my sk-123abctoken?');
    expect(result.query).not.toContain('sk-123abctoken');
    expect(result.query).toContain('[REDACTED]');
  });
});

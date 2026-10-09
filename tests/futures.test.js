// tests/futures.test.js
import { ScenarioEngine } from '../src/lib/futures/ScenarioEngine.js';
import { SimulationLab } from '../src/lib/futures/SimulationLab.js';
import { UncertaintyOptimizer } from '../src/lib/futures/UncertaintyOptimizer.js';
import { FuturesCopilot } from '../src/lib/futures/Copilot.js';

/** Feature 25 — End-to-End Validation & Production Readiness */
describe('Global Cyber Defense Simulation & Futures', () => {
  const tenantId = 'test-tenant-1';

  test('ScenarioEngine handles incomplete forecasting data safely', async () => {
    const engine = new ScenarioEngine();
    const result = await engine.forecast(tenantId, '30d', [1, 2]); // < 5 records
    expect(result.forecastData).toBe('UNKNOWN');
    expect(result.confidence).toBe(0);
  });

  test('SimulationLab Monte Carlo limits iterations', async () => {
    const lab = new SimulationLab();
    await expect(lab.runMonteCarlo(tenantId, 'scen-1', 50000, {}))
      .rejects.toThrow('Iteration limit exceeded');
  });

  test('UncertaintyOptimizer rejects fabricated confidence inputs', async () => {
    const opt = new UncertaintyOptimizer();
    await expect(opt.defineUncertainty(tenantId, 'var', {}, 0.1))
      .rejects.toThrow('UNKNOWN: Insufficient evidence for numerical estimate.');
  });

  test('FuturesCopilot redacts secrets from AI prompts', async () => {
    const copilot = new FuturesCopilot();
    const result = await copilot.interact(tenantId, 'Simulate leak of sk-supersecret99');
    expect(result.query).not.toContain('sk-supersecret99');
    expect(result.query).toContain('[REDACTED]');
  });
});

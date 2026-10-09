// tests/assurance.test.js
import { AssuranceReleaseEngine } from '../src/lib/assurance/ReleaseEngine.js';
import { AssuranceVerificationEngine } from '../src/lib/assurance/VerificationEngine.js';

/** Feature 25 — Complete End-to-End Validation & Production Readiness */
describe('Continuous Security Assurance Platform', () => {
  const tenantId = 'test-tenant-1';

  test('ReleaseEngine denies readiness if mandatory gates fail', async () => {
    const engine = new AssuranceReleaseEngine();
    const result = await engine.aggregateEvidence(tenantId, 'v1.0.0', ['PASS', 'FAIL']);
    expect(result.readinessDecision).toBe('REJECTED');
  });

  test('VerificationEngine properly flags destructive migrations for review', async () => {
    const engine = new AssuranceVerificationEngine();
    const result = await engine.validateMigration(tenantId, 'drop_table_users', true);
    expect(result.status).toBe('NEEDS_REVIEW');
  });
});

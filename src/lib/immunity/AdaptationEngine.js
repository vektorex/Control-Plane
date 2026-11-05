// src/lib/immunity/AdaptationEngine.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class AdaptationEngine {
  /**
   * Security Immunity Response Patterns (Feature 9)
   */
  async defineResponsePatterns(tenantId) {
    // Seed patterns if they do not exist
    const count = await prisma.immunityResponsePattern.count({ where: { tenantId } });
    if (count === 0) {
      await prisma.immunityResponsePattern.createMany({
        data: [
          {
            tenantId,
            patternName: 'Detection Degradation Recovery',
            trigger: 'DEGRADATION_DETECTED',
            contextRequirements: { metric: 'detectionRate' },
            recommendedResponse: { action: 'increase_validation_frequency' },
            approvalRequired: false
          },
          {
            tenantId,
            patternName: 'Emerging Attack Path Mitigation',
            trigger: 'ATTACK_PATH_EMERGING',
            contextRequirements: { severity: 'HIGH' },
            recommendedResponse: { action: 'create_engineering_work' },
            approvalRequired: true
          }
        ]
      });
    }
    return prisma.immunityResponsePattern.findMany({ where: { tenantId } });
  }

  /**
   * Continuous Defense Adaptation Engine (Feature 10)
   */
  async planAdaptation(tenantId, triggerContext) {
    const patterns = await prisma.immunityResponsePattern.findMany({
      where: { tenantId, trigger: triggerContext.type }
    });

    if (patterns.length > 0) {
      const pattern = patterns[0];
      
      const adaptation = await prisma.defenseAdaptation.create({
        data: {
          tenantId,
          actionType: pattern.recommendedResponse.action,
          targetId: triggerContext.targetId || 'system-wide',
          status: 'PENDING',
          policyEvaluated: false,
          approvalStatus: pattern.approvalRequired ? 'REQUIRED' : 'APPROVED',
          evidence: triggerContext.evidence
        }
      });
      return adaptation;
    }
    return null;
  }

  /**
   * Immunity Policy Engine (Feature 11)
   */
  async evaluatePolicy(tenantId, adaptationId) {
    const adaptation = await prisma.defenseAdaptation.findUnique({
      where: { id: adaptationId }
    });

    if (!adaptation) throw new Error('Adaptation not found');

    // Policy check logic: Never silently modify critical production security controls
    const isCritical = adaptation.actionType.includes('modify_control');
    const decision = isCritical ? 'DENIED' : 'ALLOWED';

    await prisma.immunityPolicyEvaluation.create({
      data: {
        tenantId,
        policyId: 'policy-safe-adaptation',
        decision,
        context: { action: adaptation.actionType }
      }
    });

    await prisma.defenseAdaptation.update({
      where: { id: adaptationId },
      data: { policyEvaluated: true, status: decision === 'ALLOWED' ? (adaptation.approvalStatus === 'REQUIRED' ? 'PENDING_APPROVAL' : 'EXECUTING') : 'BLOCKED' }
    });

    return decision;
  }
}

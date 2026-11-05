// src/lib/immunity/Baselines.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class BaselineEngine {
  /**
   * Security Behavior Baseline Engine 2.0 (Feature 2)
   */
  async buildSecurityBehaviorBaseline(tenantId, entityType, entityId, historicalData, context = {}) {
    // Ensure sufficient historical data is not treated as abnormal (Rule: Never treat insufficient historical data as abnormal)
    if (!historicalData || historicalData.length < 5) {
      return { status: 'INSUFFICIENT_DATA', baseline: null };
    }

    const baselineData = this.calculateBehaviorDistribution(historicalData);
    
    const baseline = await prisma.securityBehaviorBaseline.create({
      data: {
        tenantId,
        entityType,
        entityId,
        baselineData,
        seasonality: context.seasonality || 'NONE',
        environment: context.environment || 'PRODUCTION',
        confidence: 0.9,
      }
    });

    return baseline;
  }

  calculateBehaviorDistribution(data) {
    // Synthetic distribution logic
    return {
      mean: data.reduce((a, b) => a + b.value, 0) / data.length,
      variance: 0.05,
      outlierThreshold: 2.0
    };
  }

  /**
   * Defensive Immunity Baseline (Feature 3)
   */
  async buildDefenseBaseline(tenantId, controlId, performanceData) {
    const normalDetectionRate = performanceData.detectionRate || 0.99;
    const normalValidationRate = performanceData.validationRate || 0.95;
    const normalResponseLatency = performanceData.responseLatency || 150; // ms
    const normalRecoveryLatency = performanceData.recoveryLatency || 3000; // ms
    const normalControlFailures = performanceData.failures || 0;
    const normalFalsePositives = performanceData.falsePositives || 5;

    const baseline = await prisma.defenseBaseline.create({
      data: {
        tenantId,
        controlId,
        normalDetectionRate,
        normalValidationRate,
        normalResponseLatency,
        normalRecoveryLatency,
        normalControlFailures,
        normalFalsePositives,
        confidence: 0.88,
        evidence: performanceData.evidenceRefs || []
      }
    });

    return {
      baseline: baseline,
      current: performanceData,
      delta: 0, // Fresh baseline
      severity: 'NORMAL',
      confidence: baseline.confidence,
      evidence: baseline.evidence
    };
  }
}

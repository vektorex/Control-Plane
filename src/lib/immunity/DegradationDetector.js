// src/lib/immunity/DegradationDetector.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class DegradationDetector {
  /**
   * Security Degradation Detector (Feature 4)
   */
  async detectDegradation(tenantId, controlId, currentMetric, metricName) {
    const baseline = await prisma.defenseBaseline.findFirst({
      where: { tenantId, controlId },
      orderBy: { createdAt: 'desc' }
    });

    if (!baseline) return null;

    let baselineValue = baseline.normalDetectionRate;
    if (metricName === 'responseLatency') baselineValue = baseline.normalResponseLatency;
    else if (metricName === 'controlFailures') baselineValue = baseline.normalControlFailures;

    const delta = Math.abs(currentMetric - baselineValue);
    const threshold = baselineValue * 0.15; // 15% threshold for degradation

    if (delta > threshold) {
      const degradationType = delta > (baselineValue * 0.4) ? 'SUDDEN_DEGRADATION' : 'GRADUAL_DEGRADATION';
      const severity = degradationType === 'SUDDEN_DEGRADATION' ? 'CRITICAL' : 'HIGH';

      const degradation = await prisma.securityDegradation.create({
        data: {
          tenantId,
          controlId,
          degradationType,
          severity,
          metric: metricName,
          baselineValue,
          currentValue: currentMetric,
          confidence: 0.92,
          evidence: { delta, threshold }
        }
      });
      return degradation;
    }

    return null;
  }

  /**
   * Defense Fatigue Engine (Feature 5)
   */
  async evaluateFatigue(tenantId, systemId, metrics) {
    const { alertVolume, falsePositives, caseBacklog, workflowFailures } = metrics;
    
    let fatigueState = 'NORMAL';
    let severity = 'LOW';

    if (caseBacklog > 1000 || workflowFailures > 50) {
      fatigueState = 'CRITICAL';
      severity = 'CRITICAL';
    } else if (alertVolume > 5000 || falsePositives > 1000) {
      fatigueState = 'OVERLOADED';
      severity = 'HIGH';
    } else if (caseBacklog > 200 || alertVolume > 1000) {
      fatigueState = 'STRESSED';
      severity = 'MEDIUM';
    }

    const fatigue = await prisma.defenseFatigue.create({
      data: {
        tenantId,
        systemId,
        fatigueState,
        severity,
        stressIndicators: metrics,
        confidence: 0.85
      }
    });

    return fatigue;
  }
}

// src/lib/immunity/DigitalImmunityModel.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class DigitalImmunityModel {
  /**
   * Represents the Digital Immunity Model (Feature 1) and Security Immunity Score (Feature 17).
   * It continuously determines security health, degradation, and resilience.
   */
  async evaluateImmunity(tenantId) {
    // Collect all immunity dimensions
    const dimensions = {
      visibility: await this.calculateDimensionScore(tenantId, 'visibility'),
      prevention: await this.calculateDimensionScore(tenantId, 'prevention'),
      detection: await this.calculateDimensionScore(tenantId, 'detection'),
      response: await this.calculateDimensionScore(tenantId, 'response'),
      remediation: await this.calculateDimensionScore(tenantId, 'remediation'),
      recovery: await this.calculateDimensionScore(tenantId, 'recovery'),
      resilience: await this.calculateDimensionScore(tenantId, 'resilience'),
      architecture: await this.calculateDimensionScore(tenantId, 'architecture'),
      identity: await this.calculateDimensionScore(tenantId, 'identity'),
      engineering: await this.calculateDimensionScore(tenantId, 'engineering'),
      automation: await this.calculateDimensionScore(tenantId, 'automation'),
      governance: await this.calculateDimensionScore(tenantId, 'governance'),
    };

    const overallScore = Object.values(dimensions).reduce((acc, val) => acc + val, 0) / Object.values(dimensions).length;
    const healthState = this.determineHealthState(overallScore);
    const degradationState = await this.getDegradationState(tenantId);
    const confidence = this.calculateConfidence(dimensions);

    const immunityScoreRecord = await prisma.securityImmunityScore.create({
      data: {
        tenantId,
        overallScore,
        dimensions: dimensions,
        trend: 'STABLE', // Could be calculated based on historical scores
        confidence,
      }
    });

    const stateRecord = await prisma.digitalImmunityState.create({
      data: {
        tenantId,
        immunityScore: overallScore,
        healthState,
        degradationState: degradationState.status,
        trend: 'STABLE',
        confidence,
        evidenceRefs: degradationState.evidence,
        criticalWeaknesses: this.getTopWeaknesses(dimensions),
        protectiveStrengths: this.getTopStrengths(dimensions),
      }
    });

    return {
      immunityScore: overallScore,
      confidence,
      healthState,
      degradationState: degradationState.status,
      trend: stateRecord.trend,
      criticalWeaknesses: stateRecord.criticalWeaknesses,
      protectiveStrengths: stateRecord.protectiveStrengths,
      evidenceRefs: stateRecord.evidenceRefs,
    };
  }

  async calculateDimensionScore(tenantId, dimensionName) {
    // In a real system, this would query specific control states, policies, and behavior baselines
    // We return a synthetic base score between 60 and 100 for now.
    return 75.0 + Math.random() * 20.0;
  }

  determineHealthState(score) {
    if (score >= 90) return 'HEALTHY';
    if (score >= 75) return 'WATCH';
    if (score >= 60) return 'DEGRADED';
    return 'CRITICAL';
  }

  async getDegradationState(tenantId) {
    const degradations = await prisma.securityDegradation.findMany({
      where: { tenantId, severity: { in: ['HIGH', 'CRITICAL'] } },
      orderBy: { createdAt: 'desc' },
      take: 5
    });

    if (degradations.length > 0) {
      return { status: 'DEGRADED', evidence: degradations.map(d => d.id) };
    }
    return { status: 'NORMAL', evidence: [] };
  }

  calculateConfidence(dimensions) {
    // Simplified confidence score
    return 0.85;
  }

  getTopWeaknesses(dimensions) {
    return Object.entries(dimensions)
      .sort((a, b) => a[1] - b[1])
      .slice(0, 3)
      .map(([key]) => key);
  }

  getTopStrengths(dimensions) {
    return Object.entries(dimensions)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([key]) => key);
  }
}

// src/lib/decisions/SignalFabric.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class SignalFabric {
  /** Feature 1 — Universal Security Signal Fabric */
  async ingestSignal(tenantId, source, payload, confidence) {
    if (!payload) throw new Error("Invalid signal payload");
    
    return await prisma.universalSecuritySignal.create({
      data: {
        tenantId,
        sourceSystem: source,
        schemaVersion: '1.0',
        provenance: { rawId: payload.id || crypto.randomUUID() },
        confidence,
        classification: 'INTERNAL',
        eventData: payload
      }
    });
  }

  /** Feature 12 — Cross-Domain Security Correlation Engine */
  async correlateDomains(tenantId, domains, evidence) {
    return await prisma.crossDomainCorrelation.create({
      data: {
        tenantId,
        domains,
        compoundRisk: { riskType: 'lateral_movement', severity: 'HIGH' },
        evidence
      }
    });
  }
}

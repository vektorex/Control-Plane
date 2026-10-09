// src/lib/immunity/SignalQualityEngine.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class SignalQualityEngine {
  /**
   * Security Signal Quality Engine (Feature 6)
   */
  async evaluateSignalQuality(tenantId, sourceId, signalData) {
    const { completeness, freshness, duplicateRate, falsePositiveRate } = signalData;

    let qualityState = 'HIGH_VALUE_SIGNAL';
    
    if (freshness > 86400) { // older than 24h
      qualityState = 'STALE_SIGNAL';
    } else if (duplicateRate > 0.6) {
      qualityState = 'DUPLICATE_SIGNAL';
    } else if (falsePositiveRate > 0.5) {
      qualityState = 'NOISY_SIGNAL';
    } else if (completeness < 0.4) {
      qualityState = 'BLIND_SIGNAL';
    }

    const quality = await prisma.securitySignalQuality.create({
      data: {
        tenantId,
        sourceId,
        qualityState,
        metrics: signalData,
        confidence: 0.90
      }
    });

    return quality;
  }

  /**
   * Security Blind-Spot Prediction Engine (Feature 7)
   */
  async predictBlindSpots(tenantId, contextData) {
    // Context includes architecture, attack paths, asset inventory
    const blindSpots = [];

    if (!contextData.unmonitoredZones || contextData.unmonitoredZones.length > 0) {
      for (const zone of (contextData.unmonitoredZones || ['zone-x'])) {
        const spot = await prisma.securityBlindSpot.create({
          data: {
            tenantId,
            zoneId: zone,
            blindSpotType: 'unmonitored services',
            confidence: 0.75, // Predictions must have confidence
            evidence: { source: 'AssetInventory vs TelemetryCoverage' }
          }
        });
        blindSpots.push(spot);
      }
    }

    return blindSpots;
  }
}

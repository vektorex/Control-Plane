// src/lib/immunity/KnowledgeGraph.js
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class ImmunityKnowledgeGraph {
  /**
   * Security Immunity Knowledge Graph (Feature 18)
   */
  async addRelation(tenantId, sourceNode, relationType, targetNode, properties = {}) {
    const relation = await prisma.immunityGraphRelation.create({
      data: {
        tenantId,
        sourceNode,
        relationType,
        targetNode,
        properties
      }
    });
    return relation;
  }

  async getSubgraph(tenantId, node, depth = 1) {
    const relations = await prisma.immunityGraphRelation.findMany({
      where: {
        tenantId,
        OR: [
          { sourceNode: node },
          { targetNode: node }
        ]
      }
    });
    return relations;
  }
}

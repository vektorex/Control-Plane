import { apiClient } from "@/lib/api";

export const knowledgeGraphService = {
  // --- Summary & Search ---
  async getSummary(workspaceId, projectId = null) {
    return apiClient("/graph/summary", {
      params: {
        workspace_id: workspaceId,
        ...(projectId ? { project_id: projectId } : {}),
      },
    });
  },

  async searchEntities(params = {}) {
    return apiClient("/graph/entities/search", { params });
  },

  // --- Entity CRUD ---
  async listEntities(params = {}) {
    return apiClient("/graph/entities", { params });
  },

  async getEntity(entityId) {
    return apiClient(`/graph/entities/${entityId}`);
  },

  async createEntity(payload) {
    return apiClient("/graph/entities", {
      method: "POST",
      body: payload,
    });
  },

  async updateEntity(entityId, payload) {
    return apiClient(`/graph/entities/${entityId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async archiveEntity(entityId) {
    return apiClient(`/graph/entities/${entityId}`, {
      method: "DELETE",
    });
  },

  async getNeighbors(entityId, params = {}) {
    return apiClient(`/graph/entities/${entityId}/neighbors`, { params });
  },

  async mergeEntities(payload) {
    return apiClient("/graph/entities/merge", {
      method: "POST",
      body: payload,
    });
  },

  // --- Relationship CRUD ---
  async listRelationships(params = {}) {
    return apiClient("/graph/relationships", { params });
  },

  async createRelationship(payload) {
    return apiClient("/graph/relationships", {
      method: "POST",
      body: payload,
    });
  },

  async updateRelationship(relationshipId, payload) {
    return apiClient(`/graph/relationships/${relationshipId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async archiveRelationship(relationshipId) {
    return apiClient(`/graph/relationships/${relationshipId}`, {
      method: "DELETE",
    });
  },

  // --- Graph Traversal / Query / Preview / Extraction ---
  async queryGraph(payload) {
    return apiClient("/graph/query", {
      method: "POST",
      body: payload,
    });
  },

  async extractGraph(payload) {
    return apiClient("/graph/extract", {
      method: "POST",
      body: payload,
    });
  },

  async previewGraph(payload) {
    return apiClient("/graph/preview", {
      method: "POST",
      body: payload,
    });
  },

  async previewTaskGraph(taskId) {
    return apiClient(`/tasks/${taskId}/graph/preview`, {
      method: "POST",
    });
  },

  // --- Proposals & HITL Review ---
  async listProposals(params = {}) {
    return apiClient("/graph/proposals", { params });
  },

  async getProposal(proposalId) {
    return apiClient(`/graph/proposals/${proposalId}`);
  },

  async approveProposal(proposalId, payload = {}) {
    return apiClient(`/graph/proposals/${proposalId}/approve`, {
      method: "POST",
      body: payload,
    });
  },

  async rejectProposal(proposalId, payload = {}) {
    return apiClient(`/graph/proposals/${proposalId}/reject`, {
      method: "POST",
      body: payload,
    });
  },

  // --- Conflicts ---
  async listConflicts(params = {}) {
    return apiClient("/graph/conflicts", { params });
  },

  async getConflict(conflictId) {
    return apiClient(`/graph/conflicts/${conflictId}`);
  },

  async resolveConflict(conflictId, payload) {
    return apiClient(`/graph/conflicts/${conflictId}/resolve`, {
      method: "POST",
      body: payload,
    });
  },
};

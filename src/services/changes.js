import { apiClient } from "@/lib/api";

export const changesService = {
  async listChangeRequests(params = {}) {
    return apiClient("/changes", { params });
  },

  async getChangeRequest(changeId) {
    return apiClient(`/changes/${changeId}`);
  },

  async createChangeRequest(payload) {
    return apiClient("/changes", {
      method: "POST",
      body: payload,
    });
  },

  async parseChange(changeId) {
    return apiClient(`/changes/${changeId}/parse`, {
      method: "POST",
    });
  },

  async analyzeChange(changeId) {
    return apiClient(`/changes/${changeId}/analyze`, {
      method: "POST",
    });
  },

  async analyzeImpact(changeId) {
    return this.analyzeChange(changeId);
  },

  async getImpact(changeId) {
    return apiClient(`/changes/${changeId}/impact`);
  },

  async getDependencies(changeId) {
    return apiClient(`/changes/${changeId}/dependencies`);
  },

  async getRisks(changeId) {
    return apiClient(`/changes/${changeId}/risks`);
  },

  async getEvidence(changeId) {
    return apiClient(`/changes/${changeId}/evidence`);
  },

  async getRollback(changeId) {
    return apiClient(`/changes/${changeId}/rollback`);
  },
};

export const changeService = changesService;
export default changesService;

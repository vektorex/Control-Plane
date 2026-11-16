import { apiClient } from "@/lib/api";

export const intentService = {
  async listIntents(params = {}) {
    return apiClient("/intent", { params });
  },

  async getIntent(requestId) {
    return apiClient(`/intent/${requestId}`);
  },

  async createIntent(payload) {
    return apiClient("/intent", {
      method: "POST",
      body: payload,
    });
  },

  async analyzeIntent(requestId) {
    return apiClient(`/intent/${requestId}/analyze`, {
      method: "POST",
    });
  },

  async validateCandidate(requestId, candidateId) {
    return apiClient(`/intent/${requestId}/candidates/${candidateId}/validate`, {
      method: "POST",
    });
  },

  async simulateCandidate(requestId, candidateId) {
    return apiClient(`/intent/${requestId}/candidates/${candidateId}/simulate`, {
      method: "POST",
    });
  },

  async createIntentRequest(payload) {
    return this.createIntent(payload);
  },

  async getIntentRequest(requestId) {
    return this.getIntent(requestId);
  },

  async answerClarification(requestId, clarificationId, payload) {
    return apiClient(`/intent/${requestId}/clarifications/${clarificationId}`, {
      method: "POST",
      body: payload,
    });
  },

  async synthesizeCandidates(requestId) {
    return apiClient(`/intent/${requestId}/candidates`, {
      method: "POST",
    });
  },
};

export default intentService;

import { apiClient } from "@/lib/api";

export const rolloutsService = {
  async listRollouts(params = {}) {
    return apiClient("/rollouts", { params });
  },

  async getRollout(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}`);
  },

  async createRollout(payload) {
    return apiClient("/rollouts", {
      method: "POST",
      body: payload,
    });
  },

  async validateRollout(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/validate`, {
      method: "POST",
    });
  },

  async startRollout(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/start`, {
      method: "POST",
    });
  },

  async pauseRollout(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/pause`, {
      method: "POST",
    });
  },

  async resumeRollout(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/resume`, {
      method: "POST",
    });
  },

  async abortRollout(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/abort`, {
      method: "POST",
    });
  },

  async getStages(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/stages`);
  },

  async getHealth(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/health`);
  },

  async getEvidence(rolloutId) {
    return apiClient(`/rollouts/${rolloutId}/evidence`);
  },
};

export const rolloutService = rolloutsService;
export default rolloutsService;

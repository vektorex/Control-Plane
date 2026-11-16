import { apiClient } from "@/lib/api";

export const releasesService = {
  async listReleases(params = {}) {
    return apiClient("/releases", { params });
  },

  async getRelease(releaseId) {
    return apiClient(`/releases/${releaseId}`);
  },

  async createRelease(payload) {
    return apiClient("/releases", {
      method: "POST",
      body: payload,
    });
  },

  async buildReleasePlan(releaseId) {
    return apiClient(`/releases/${releaseId}/build-plan`, {
      method: "POST",
    });
  },

  async getReleasePlan(releaseId) {
    return apiClient(`/releases/${releaseId}/plan`);
  },

  async validateRelease(releaseId) {
    return apiClient(`/releases/${releaseId}/validate`, {
      method: "POST",
    });
  },

  async stageRelease(releaseId) {
    return apiClient(`/releases/${releaseId}/stage`, {
      method: "POST",
    });
  },

  async promoteRelease(releaseId) {
    return apiClient(`/releases/${releaseId}/promote`, {
      method: "POST",
    });
  },

  async rollbackRelease(releaseId) {
    return apiClient(`/releases/${releaseId}/rollback`, {
      method: "POST",
    });
  },

  async getEvidence(releaseId) {
    return apiClient(`/releases/${releaseId}/evidence`);
  },

  async getTimeline(releaseId) {
    return apiClient(`/releases/${releaseId}/timeline`);
  },
};

export const releaseService = releasesService;
export default releasesService;

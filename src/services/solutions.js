import { apiClient } from "@/lib/api";

export const solutionsService = {
  async listSolutions(params = {}) {
    return apiClient("/solutions", { params });
  },

  async getSolution(solutionId) {
    return apiClient(`/solutions/${solutionId}`);
  },

  async createSolution(payload) {
    return apiClient("/solutions", {
      method: "POST",
      body: payload,
    });
  },

  async updateSolution(solutionId, payload) {
    return apiClient(`/solutions/${solutionId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async listVersions(solutionId) {
    return apiClient(`/solutions/${solutionId}/versions`);
  },

  async validateSolution(solutionId) {
    return apiClient(`/solutions/${solutionId}/validate`, {
      method: "POST",
    });
  },

  async publishSolution(solutionId) {
    return apiClient(`/solutions/${solutionId}/publish`, {
      method: "POST",
    });
  },

  async getDependencies(solutionId) {
    return apiClient(`/solutions/${solutionId}/dependencies`);
  },
};

export const solutionService = solutionsService;
export default solutionsService;

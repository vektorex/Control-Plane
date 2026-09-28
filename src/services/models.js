import { apiClient } from "@/lib/api";

export const modelService = {
  /**
   * List safe model catalog metadata for the current user
   */
  async listModels() {
    return apiClient("/models");
  },

  /**
   * Preview deterministic model routing based on specific requirements
   */
  async routeModel(payload) {
    return apiClient("/models/route", {
      method: "POST",
      body: payload,
    });
  },
};

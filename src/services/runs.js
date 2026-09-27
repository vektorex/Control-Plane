import { apiClient } from "@/lib/api";

export const runService = {
  /**
   * Retrieve a single run detail by ID (with ownership validation)
   */
  async getRun(runId) {
    return apiClient(`/runs/${runId}`);
  },
};

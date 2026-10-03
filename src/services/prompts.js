import { apiClient } from "@/lib/api";

export const promptService = {
  // --- Prompt CRUD ---
  async listPrompts(params = {}) {
    return apiClient("/prompts", { params });
  },

  async getPrompt(promptId) {
    return apiClient(`/prompts/${promptId}`);
  },

  async createPrompt(payload) {
    return apiClient("/prompts", {
      method: "POST",
      body: payload,
    });
  },

  async updatePrompt(promptId, payload) {
    return apiClient(`/prompts/${promptId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async archivePrompt(promptId) {
    return apiClient(`/prompts/${promptId}`, {
      method: "DELETE",
    });
  },

  async seedPrompts(workspaceId, projectId = null) {
    return apiClient("/prompts/seed", {
      method: "POST",
      params: { workspace_id: workspaceId, ...(projectId ? { project_id: projectId } : {}) },
    });
  },

  // --- Versions ---
  async listVersions(promptId) {
    return apiClient(`/prompts/${promptId}/versions`);
  },

  async getVersion(promptId, versionId) {
    return apiClient(`/prompts/${promptId}/versions/${versionId}`);
  },

  async createVersion(promptId, payload) {
    return apiClient(`/prompts/${promptId}/versions`, {
      method: "POST",
      body: payload,
    });
  },

  async publishVersion(promptId, versionId) {
    return apiClient(`/prompts/${promptId}/versions/${versionId}/publish`, {
      method: "POST",
    });
  },

  async compareVersions(promptId, baseVersionId, targetVersionId) {
    return apiClient(`/prompts/${promptId}/versions/diff`, {
      params: {
        base_version_id: baseVersionId,
        target_version_id: targetVersionId,
      },
    });
  },

  // --- Releases ---
  async listReleases(promptId) {
    return apiClient(`/prompts/${promptId}/releases`);
  },

  async createRelease(promptId, payload) {
    return apiClient(`/prompts/${promptId}/releases`, {
      method: "POST",
      body: payload,
    });
  },

  async rollbackRelease(promptId, payload) {
    return apiClient(`/prompts/${promptId}/rollback`, {
      method: "POST",
      body: payload,
    });
  },

  async resolvePrompt(promptId, environment = "production") {
    return apiClient(`/prompts/${promptId}/resolve`, {
      params: { environment },
    });
  },

  // --- Preview & Testing ---
  async previewPrompt(promptId, payload) {
    return apiClient(`/prompts/${promptId}/preview`, {
      method: "POST",
      body: payload,
    });
  },

  async testPrompt(promptId, payload) {
    return apiClient(`/prompts/${promptId}/test`, {
      method: "POST",
      body: payload,
    });
  },

  // --- Experiments ---
  async listExperiments(params = {}) {
    return apiClient("/prompt-experiments", { params });
  },

  async getExperiment(experimentId) {
    return apiClient(`/prompt-experiments/${experimentId}`);
  },

  async createExperiment(payload) {
    return apiClient("/prompt-experiments", {
      method: "POST",
      body: payload,
    });
  },

  async updateExperiment(experimentId, payload) {
    return apiClient(`/prompt-experiments/${experimentId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async addVariant(experimentId, payload) {
    return apiClient(`/prompt-experiments/${experimentId}/variants`, {
      method: "POST",
      body: payload,
    });
  },

  async startExperiment(experimentId) {
    return apiClient(`/prompt-experiments/${experimentId}/start`, {
      method: "POST",
    });
  },

  async pauseExperiment(experimentId) {
    return apiClient(`/prompt-experiments/${experimentId}/pause`, {
      method: "POST",
    });
  },

  async completeExperiment(experimentId) {
    return apiClient(`/prompt-experiments/${experimentId}/complete`, {
      method: "POST",
    });
  },

  async getExperimentResults(experimentId) {
    return apiClient(`/prompt-experiments/${experimentId}/results`);
  },
};

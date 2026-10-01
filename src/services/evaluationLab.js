import { apiClient } from "@/lib/api";

/**
 * Client service for AI Evaluation Lab (Step 22).
 * Supports dataset management, versioning, case assertions,
 * repeatable experiment execution, factual comparisons, and continuous regression detection.
 */
export const evaluationLabService = {
  // --- Datasets ---
  async listDatasets({ status = null, limit = 50, offset = 0 } = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    const query = new URLSearchParams();
    if (status) query.set("status", status);
    query.set("limit", limit);
    query.set("offset", offset);
    return apiClient(`/evaluation/datasets?${query.toString()}`, { headers });
  },

  async getDataset(datasetId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/datasets/${datasetId}`, { headers });
  },

  async createDataset(data, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient("/evaluation/datasets", {
      method: "POST",
      headers,
      body: data,
    });
  },

  async updateDataset(datasetId, data, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/datasets/${datasetId}`, {
      method: "PATCH",
      headers,
      body: data,
    });
  },

  async createDatasetVersion(datasetId, data = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/datasets/${datasetId}/versions`, {
      method: "POST",
      headers,
      body: data,
    });
  },

  async importCases(datasetId, { fileFormat, content, targetVersionId }, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/datasets/${datasetId}/import`, {
      method: "POST",
      headers,
      body: {
        file_format: fileFormat,
        content,
        target_version_id: targetVersionId || undefined,
      },
    });
  },

  async exportCases(datasetId, format = "json", versionId = null, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    const query = new URLSearchParams({ format });
    if (versionId) query.set("version_id", versionId);
    return apiClient(`/evaluation/datasets/${datasetId}/export?${query.toString()}`, {
      headers,
    });
  },

  // --- Cases ---
  async listCases(datasetId, { versionId = null, limit = 100, offset = 0 } = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    const query = new URLSearchParams();
    if (versionId) query.set("version_id", versionId);
    query.set("limit", limit);
    query.set("offset", offset);
    return apiClient(`/evaluation/datasets/${datasetId}/cases?${query.toString()}`, { headers });
  },

  async getCase(caseId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/cases/${caseId}`, { headers });
  },

  async createCase(datasetId, caseData, versionId = null, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    const query = versionId ? `?version_id=${versionId}` : "";
    return apiClient(`/evaluation/datasets/${datasetId}/cases${query}`, {
      method: "POST",
      headers,
      body: caseData,
    });
  },

  async updateCase(caseId, caseData, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/cases/${caseId}`, {
      method: "PATCH",
      headers,
      body: caseData,
    });
  },

  async deleteCase(caseId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/cases/${caseId}`, {
      method: "DELETE",
      headers,
    });
  },

  // --- Experiments ---
  async listExperiments({ status = null, targetType = null, limit = 50, offset = 0 } = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    const query = new URLSearchParams();
    if (status) query.set("status", status);
    if (targetType) query.set("target_type", targetType);
    query.set("limit", limit);
    query.set("offset", offset);
    return apiClient(`/evaluation/experiments?${query.toString()}`, { headers });
  },

  async getExperiment(experimentId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/experiments/${experimentId}`, { headers });
  },

  async createExperiment(data, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient("/evaluation/experiments", {
      method: "POST",
      headers,
      body: data,
    });
  },

  async runExperiment(experimentId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/experiments/${experimentId}/run`, {
      method: "POST",
      headers,
    });
  },

  async cancelExperiment(experimentId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/experiments/${experimentId}/cancel`, {
      method: "POST",
      headers,
    });
  },

  async getExperimentResults(experimentId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/experiments/${experimentId}/results`, { headers });
  },

  async getExperimentTrace(experimentId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/evaluation/experiments/${experimentId}/trace`, { headers });
  },

  // --- Comparisons & Regressions ---
  async compareExperiments(experimentA, experimentB, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient("/evaluation/compare", {
      method: "POST",
      headers,
      body: {
        experiment_a: experimentA,
        experiment_b: experimentB,
      },
    });
  },

  async checkRegressions(baselineExperiment, candidateExperiment, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient("/evaluation/regressions/check", {
      method: "POST",
      headers,
      body: {
        baseline_experiment: baselineExperiment,
        candidate_experiment: candidateExperiment,
      },
    });
  },
};

import { apiClient } from "@/lib/api";

export const analyticsService = {
  /**
   * Retrieve high-level overview metrics (runs, tokens, cost, latency, eval passes)
   */
  async getOverview(params = {}) {
    return apiClient("/analytics/overview", { params });
  },

  /**
   * Retrieve time-series usage metrics (tokens, runs, cost over time)
   */
  async getUsage(params = {}) {
    return apiClient("/analytics/usage", { params });
  },

  /**
   * Retrieve model-level analytics (usage, tokens, latency, cost, errors, capabilities)
   */
  async getModels(params = {}) {
    return apiClient("/analytics/models", { params });
  },

  /**
   * Retrieve provider-level analytics (market share, tokens, cost, latency)
   */
  async getProviders(params = {}) {
    return apiClient("/analytics/providers", { params });
  },

  /**
   * Retrieve overall and per-stage latency breakdown (planning, retrieval, tools, generation, eval)
   */
  async getLatency(params = {}) {
    return apiClient("/analytics/latency", { params });
  },

  /**
   * Retrieve evaluation metrics (passed, warnings, failures, revision counts, common issues)
   */
  async getEvaluations(params = {}) {
    return apiClient("/analytics/evaluations", { params });
  },

  /**
   * Retrieve execution trace timeline for a run
   */
  async getRunTrace(runId) {
    return apiClient(`/runs/${runId}/trace`);
  },

  /**
   * Retrieve usage records breakdown for a run
   */
  async getRunUsage(runId) {
    return apiClient(`/runs/${runId}/usage`);
  },

  /**
   * Retrieve consolidated RunTelemetry for a run
   */
  async getRunTelemetry(runId) {
    return apiClient(`/runs/${runId}/telemetry`);
  },

  /**
   * Trigger retention cleanup for telemetry and trace events (admin/workspace owner)
   */
  async cleanupObservability(params = {}) {
    return apiClient("/admin/observability/cleanup", {
      method: "POST",
      params,
    });
  },
};

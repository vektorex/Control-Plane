import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 35: AI Reliability, Resilience & Chaos Engineering Layer.
 */
export const reliabilityService = {
  /**
   * Fetch system health state.
   */
  async getHealth() {
    return apiClient("/reliability/health");
  },

  /**
   * Fetch reliability overview counts and component breakdown.
   */
  async getOverview() {
    return apiClient("/reliability/overview");
  },

  /**
   * List registered components with status and health filters.
   */
  async listComponents(params = {}) {
    return apiClient("/reliability/components", {
      params: {
        component_type: params.componentType,
        health_status: params.healthStatus,
        status: params.status,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Get single component details.
   */
  async getComponent(componentId) {
    return apiClient(`/reliability/components/${componentId}`);
  },

  /**
   * List lightweight dependency checks.
   */
  async listDependencies(params = {}) {
    return apiClient("/reliability/dependencies", {
      params: {
        component_id: params.componentId,
        status: params.status,
        limit: params.limit || 50,
      },
    });
  },

  /**
   * List execution checkpoints with filters.
   */
  async listCheckpoints(params = {}) {
    return apiClient("/reliability/checkpoints", {
      params: {
        run_id: params.runId,
        workflow_run_id: params.workflowRunId,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Get single checkpoint.
   */
  async getCheckpoint(checkpointId) {
    return apiClient(`/reliability/checkpoints/${checkpointId}`);
  },

  /**
   * Safely resume execution from checkpoint boundary.
   */
  async resumeCheckpoint(checkpointId, data) {
    return apiClient(`/reliability/checkpoints/${checkpointId}/resume`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List reliability objectives (SLOs).
   */
  async listObjectives() {
    return apiClient("/reliability/objectives");
  },

  /**
   * List operational failure budgets.
   */
  async listBudgets() {
    return apiClient("/reliability/budgets");
  },

  /**
   * List chaos experiments.
   */
  async listExperiments(params = {}) {
    return apiClient("/reliability/experiments", {
      params: {
        environment: params.environment,
        status: params.status,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Create chaos experiment.
   */
  async createExperiment(data) {
    return apiClient("/reliability/experiments", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get single chaos experiment details with runs and observations.
   */
  async getExperiment(experimentId) {
    return apiClient(`/reliability/experiments/${experimentId}`);
  },

  /**
   * Get safety blast radius summary for experiment.
   */
  async getExperimentSafetySummary(experimentId) {
    return apiClient(`/reliability/experiments/${experimentId}/safety-summary`);
  },

  /**
   * Approve chaos experiment.
   */
  async approveExperiment(experimentId) {
    return apiClient(`/reliability/experiments/${experimentId}/approve`, {
      method: "POST",
    });
  },

  /**
   * Run chaos experiment.
   */
  async runExperiment(experimentId) {
    return apiClient(`/reliability/experiments/${experimentId}/run`, {
      method: "POST",
    });
  },

  /**
   * Abort in-flight chaos experiment.
   */
  async abortExperiment(experimentId, reason) {
    return apiClient(`/reliability/experiments/${experimentId}/abort`, {
      method: "POST",
      params: { reason },
    });
  },

  /**
   * Get operational telemetry metrics.
   */
  async getTelemetry(params = {}) {
    return apiClient("/reliability/telemetry", {
      params: {
        days: params.days || 30,
      },
    });
  },

  /**
   * Get bulkhead capacity and slots.
   */
  async getBulkheads() {
    return apiClient("/reliability/bulkheads");
  },

  /**
   * Get circuit breaker statuses.
   */
  async getCircuits() {
    return apiClient("/reliability/circuits");
  },
};

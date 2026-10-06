import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 41: AI Agent Simulation, Sandbox & Scenario Testing Layer.
 */
export const simulationService = {
  // ---------------------------------------------------------------------------
  // Simulations CRUD
  // ---------------------------------------------------------------------------

  async listSimulations(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.targetType) q.set("target_type", params.targetType);
    if (params.targetId) q.set("target_id", params.targetId);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/simulations${qs ? `?${qs}` : ""}`);
  },

  async getSimulation(simulationId) {
    return apiClient(`/simulations/${simulationId}`);
  },

  async createSimulation(data) {
    return apiClient("/simulations", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateSimulation(simulationId, data) {
    return apiClient(`/simulations/${simulationId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async createVersion(simulationId, data) {
    return apiClient(`/simulations/${simulationId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async runSimulation(simulationId, data = {}) {
    return apiClient(`/simulations/${simulationId}/run`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listSimulationRuns(simulationId, params = {}) {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/simulations/${simulationId}/runs${qs ? `?${qs}` : ""}`);
  },

  // ---------------------------------------------------------------------------
  // Scenarios CRUD
  // ---------------------------------------------------------------------------

  async listScenarios(params = {}) {
    const q = new URLSearchParams();
    if (params.scenarioType) q.set("scenario_type", params.scenarioType);
    if (params.simulationVersionId) q.set("simulation_version_id", params.simulationVersionId);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/simulation-scenarios${qs ? `?${qs}` : ""}`);
  },

  async getScenario(scenarioId) {
    return apiClient(`/simulation-scenarios/${scenarioId}`);
  },

  async createScenario(data) {
    return apiClient("/simulation-scenarios", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateScenario(scenarioId, data) {
    return apiClient(`/simulation-scenarios/${scenarioId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ---------------------------------------------------------------------------
  // Suites CRUD & Run
  // ---------------------------------------------------------------------------

  async listSuites(params = {}) {
    const q = new URLSearchParams();
    if (params.targetType) q.set("target_type", params.targetType);
    if (params.targetId) q.set("target_id", params.targetId);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/simulation-suites${qs ? `?${qs}` : ""}`);
  },

  async getSuite(suiteId) {
    return apiClient(`/simulation-suites/${suiteId}`);
  },

  async createSuite(data) {
    return apiClient("/simulation-suites", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async runSuite(suiteId, data = {}) {
    return apiClient(`/simulation-suites/${suiteId}/run`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ---------------------------------------------------------------------------
  // Runs, Trace, Report, Side Effects, Comparison
  // ---------------------------------------------------------------------------

  async getRun(runId) {
    return apiClient(`/simulation-runs/${runId}`);
  },

  async getRunTrace(runId) {
    return apiClient(`/simulation-runs/${runId}/trace`);
  },

  async getRunReport(runId) {
    return apiClient(`/simulation-runs/${runId}/report`);
  },

  async getRunSideEffects(runId) {
    return apiClient(`/simulation-runs/${runId}/side-effects`);
  },

  async getRunAssertions(runId) {
    return apiClient(`/simulation-runs/${runId}/assertions`);
  },

  async compareRuns(runId, comparisonRunId) {
    return apiClient(`/simulation-runs/${runId}/compare`, {
      method: "POST",
      body: JSON.stringify({ comparison_run_id: comparisonRunId }),
      headers: { "Content-Type": "application/json" },
    });
  },
};

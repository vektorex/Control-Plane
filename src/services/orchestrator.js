import { apiClient } from "@/lib/api";

/**
 * Service contracts for the Python/FastAPI Orchestration Layer.
 * Future backend endpoints will integrate seamlessly with these interfaces.
 */
export const orchestratorService = {
  /**
   * Health check to verify FastAPI orchestration backend status
   */
  async getHealth() {
    return apiClient("/health");
  },

  /**
   * Fetch system engine stats and active execution metrics
   */
  async getMetrics() {
    return apiClient("/metrics");
  },

  /**
   * List orchestrated work tasks with optional filtering
   */
  async getTasks(params = {}) {
    return apiClient("/tasks", { params });
  },

  /**
   * Retrieve a single task's execution graph and status
   */
  async getTask(taskId) {
    return apiClient(`/tasks/${taskId}`);
  },

  /**
   * Create and submit a task to the orchestration queue
   */
  async createTask(payload) {
    return apiClient("/tasks", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * List registered projects/workspaces
   */
  async getProjects() {
    return apiClient("/projects");
  },

  /**
   * Create a new project workspace
   */
  async createProject(payload) {
    return apiClient("/projects", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Retrieve orchestrator engine settings & provider statuses
   */
  async getOrchestratorConfig() {
    return apiClient("/settings/orchestration");
  },

  /**
   * Update orchestrator engine settings
   */
  async updateOrchestratorConfig(payload) {
    return apiClient("/settings/orchestration", {
      method: "PUT",
      body: payload,
    });
  },
};

import { apiClient } from "@/lib/api";

export const workflowService = {
  /**
   * List workflows with optional workspace/project/status filters and pagination
   */
  async listWorkflows(params = {}) {
    return apiClient("/workflows", { params });
  },

  /**
   * Retrieve a single workflow by ID
   */
  async getWorkflow(workflowId) {
    return apiClient(`/workflows/${workflowId}`);
  },

  /**
   * Create a new workflow
   */
  async createWorkflow(payload) {
    return apiClient("/workflows", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Update workflow metadata
   */
  async updateWorkflow(workflowId, payload) {
    return apiClient(`/workflows/${workflowId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Delete a workflow
   */
  async deleteWorkflow(workflowId) {
    return apiClient(`/workflows/${workflowId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get full workflow definition (steps, schema, configuration)
   */
  async getWorkflowDefinition(workflowId) {
    return apiClient(`/workflows/${workflowId}/definition`);
  },

  /**
   * Update workflow definition (steps, schema, configuration)
   */
  async updateWorkflowDefinition(workflowId, payload) {
    return apiClient(`/workflows/${workflowId}/definition`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Validate workflow definition rules and constraints
   */
  async validateWorkflow(workflowId) {
    return apiClient(`/workflows/${workflowId}/validate`, {
      method: "POST",
    });
  },

  /**
   * Publish workflow version (makes version snapshot immutable)
   */
  async publishWorkflow(workflowId) {
    return apiClient(`/workflows/${workflowId}/publish`, {
      method: "POST",
    });
  },

  /**
   * Duplicate a workflow into a new draft
   */
  async duplicateWorkflow(workflowId) {
    return apiClient(`/workflows/${workflowId}/duplicate`, {
      method: "POST",
    });
  },

  /**
   * Execute a workflow run
   */
  async runWorkflow(workflowId, payload = {}) {
    return apiClient(`/workflows/${workflowId}/run`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * List historical runs for a workflow
   */
  async listWorkflowRuns(workflowId, params = {}) {
    return apiClient(`/workflows/${workflowId}/runs`, { params });
  },

  /**
   * Retrieve a specific workflow run by ID
   */
  async getWorkflowRun(runId) {
    return apiClient(`/workflow-runs/${runId}`);
  },

  /**
   * Retrieve observability execution trace for a workflow run
   */
  async getWorkflowRunTrace(runId) {
    return apiClient(`/workflow-runs/${runId}/trace`);
  },

  /**
   * List built-in workflow templates
   */
  async listTemplates() {
    return apiClient("/workflow-templates");
  },

  /**
   * Install a built-in template into the active workspace
   */
  async installTemplate(templateId, payload = {}) {
    return apiClient(`/workflow-templates/${templateId}/install`, {
      method: "POST",
      body: payload,
    });
  },
};

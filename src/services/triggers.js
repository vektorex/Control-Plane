import { apiClient } from "@/lib/api";

export const triggerService = {
  /**
   * List all triggers for a specific workflow
   */
  async listTriggers(workflowId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/workflows/${workflowId}/triggers`, { params });
  },

  /**
   * Get a single trigger by ID
   */
  async getTrigger(triggerId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}`, { params });
  },

  /**
   * Create a new trigger for a workflow
   */
  async createTrigger(workflowId, payload, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/workflows/${workflowId}/triggers`, {
      method: "POST",
      params,
      body: payload,
    });
  },

  /**
   * Update trigger configuration or metadata
   */
  async updateTrigger(triggerId, payload, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}`, {
      method: "PATCH",
      params,
      body: payload,
    });
  },

  /**
   * Delete a trigger
   */
  async deleteTrigger(triggerId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}`, {
      method: "DELETE",
      params,
    });
  },

  /**
   * Pause trigger execution
   */
  async pauseTrigger(triggerId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}/pause`, {
      method: "POST",
      params,
    });
  },

  /**
   * Resume paused trigger
   */
  async resumeTrigger(triggerId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}/resume`, {
      method: "POST",
      params,
    });
  },

  /**
   * Dry-run test mode: evaluate filters & variable mapping without side effects
   */
  async testTrigger(triggerId, payload, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}/test`, {
      method: "POST",
      params,
      body: payload,
    });
  },

  /**
   * Manually execute a trigger synchronously
   */
  async runManualTrigger(workflowId, triggerId, inputData = {}, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/workflows/${workflowId}/triggers/${triggerId}/run`, {
      method: "POST",
      params,
      body: { input_data: inputData },
    });
  },

  /**
   * List historical runs for a trigger
   */
  async listTriggerRuns(triggerId, workspaceId, params = {}) {
    const query = { ...(workspaceId ? { workspace_id: workspaceId } : {}), ...params };
    return apiClient(`/triggers/${triggerId}/runs`, { params: query });
  },

  /**
   * Get single trigger run detail
   */
  async getTriggerRun(triggerRunId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/trigger-runs/${triggerRunId}`, { params });
  },

  /**
   * Regenerate webhook verification secret
   */
  async regenerateWebhookSecret(triggerId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}/webhook/regenerate-secret`, {
      method: "POST",
      params,
    });
  },

  /**
   * Get webhook connection status and public URL
   */
  async getWebhookStatus(triggerId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/triggers/${triggerId}/webhook/status`, { params });
  },
};

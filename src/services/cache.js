import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 31: Production-Grade Semantic Cache and Intelligent Reuse Layer.
 */
export const cacheService = {
  /**
   * Fetch factual cache metrics and telemetry.
   */
  async getStats(workspaceId) {
    return apiClient("/cache/stats", {
      params: { workspace_id: workspaceId },
    });
  },

  /**
   * Fetch workspace cache policy configuration.
   */
  async getPolicy(workspaceId) {
    return apiClient("/cache/policy", {
      params: { workspace_id: workspaceId },
    });
  },

  /**
   * Update workspace cache policy configuration (admin only).
   */
  async updatePolicy(workspaceId, policy) {
    return apiClient("/cache/policy", {
      method: "PUT",
      params: { workspace_id: workspaceId },
      body: JSON.stringify(policy),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Surgically invalidate cache entries across various scopes.
   */
  async invalidate(data) {
    return apiClient("/cache/invalidate", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Probe cache eligibility and match candidates without running execution.
   */
  async preview(data) {
    return apiClient("/cache/preview", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * List sanitized cache entries with pagination.
   */
  async listEntries({ workspaceId, namespace, status, limit = 50, offset = 0 } = {}) {
    return apiClient("/cache/entries", {
      params: {
        workspace_id: workspaceId,
        namespace,
        status,
        limit,
        offset,
      },
    });
  },

  /**
   * Get single sanitized cache entry by ID.
   */
  async getEntry(entryId, workspaceId) {
    return apiClient(`/cache/entries/${entryId}`, {
      params: { workspace_id: workspaceId },
    });
  },

  /**
   * Invalidate / delete single cache entry.
   */
  async deleteEntry(entryId, workspaceId) {
    return apiClient(`/cache/entries/${entryId}`, {
      method: "DELETE",
      params: { workspace_id: workspaceId },
    });
  },
};

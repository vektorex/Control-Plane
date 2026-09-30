import { apiClient } from "@/lib/api";

/**
 * Service methods for the Memory & Persistent Context Intelligence System (Step 17).
 */
export const memoryService = {
  /**
   * List memories with optional filtering by scope, type, status, project_id, search
   */
  async listMemories(params = {}) {
    const query = new URLSearchParams();
    if (params.scope) query.set("scope", params.scope);
    if (params.type) query.set("type", params.type);
    if (params.status) query.set("status", params.status);
    if (params.project_id) query.set("project_id", params.project_id);
    if (params.search) query.set("search", params.search);
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return apiClient(`/memories${queryString}`);
  },

  /**
   * Retrieve single memory by ID
   */
  async getMemory(memoryId) {
    return apiClient(`/memories/${memoryId}`);
  },

  /**
   * Explicitly create a new persistent memory
   */
  async createMemory(data) {
    return apiClient("/memories", {
      method: "POST",
      body: data,
    });
  },

  /**
   * Update an existing memory
   */
  async updateMemory(memoryId, data) {
    return apiClient(`/memories/${memoryId}`, {
      method: "PATCH",
      body: data,
    });
  },

  /**
   * Delete a memory permanently
   */
  async deleteMemory(memoryId) {
    return apiClient(`/memories/${memoryId}`, {
      method: "DELETE",
    });
  },

  /**
   * Archive memory so it is excluded from future retrieval
   */
  async archiveMemory(memoryId) {
    return apiClient(`/memories/${memoryId}/archive`, {
      method: "POST",
    });
  },

  /**
   * Restore archived memory back to active status
   */
  async restoreMemory(memoryId) {
    return apiClient(`/memories/${memoryId}/restore`, {
      method: "POST",
    });
  },

  /**
   * Mark memory as used (updates last_used_at and usage telemetry)
   */
  async useMemory(memoryId) {
    return apiClient(`/memories/${memoryId}/use`, {
      method: "POST",
    });
  },

  /**
   * User-initiated save as memory from connector snippet or document fact
   */
  async saveFromSource(data) {
    return apiClient("/memories/from-source", {
      method: "POST",
      body: data,
    });
  },

  /**
   * List pending AI-suggested candidate memories
   */
  async listSuggestions(status = "candidate") {
    const query = status ? `?status=${status}` : "";
    return apiClient(`/memories/suggestions${query}`);
  },

  /**
   * Accept candidate memory suggestion to make it permanent
   */
  async acceptSuggestion(suggestionId, data = {}) {
    return apiClient(`/memories/suggestions/${suggestionId}/accept`, {
      method: "POST",
      body: data,
    });
  },

  /**
   * Reject candidate suggestion so it is discarded
   */
  async rejectSuggestion(suggestionId) {
    return apiClient(`/memories/suggestions/${suggestionId}/reject`, {
      method: "POST",
    });
  },

  /**
   * List detected conflicting memories
   */
  async listConflicts(status = "unresolved") {
    const query = status ? `?status=${status}` : "";
    return apiClient(`/memories/conflicts${query}`);
  },

  /**
   * Resolve a conflicting memory pair
   */
  async resolveConflict(conflictId, data) {
    return apiClient(`/memories/conflicts/${conflictId}/resolve`, {
      method: "POST",
      body: data,
    });
  },

  /**
   * Get user memory settings
   */
  async getSettings() {
    return apiClient("/memories/settings");
  },

  /**
   * Update user memory settings
   */
  async updateSettings(data) {
    return apiClient("/memories/settings", {
      method: "PUT",
      body: data,
    });
  },

  /**
   * Privacy bulk purge of memories in a scope ('project' or 'workspace')
   */
  async deleteByScope(scope, projectId = null) {
    const query = projectId ? `?project_id=${projectId}` : "";
    return apiClient(`/memories/scope/${scope}${query}`, {
      method: "DELETE",
    });
  },
};

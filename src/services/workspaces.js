import { apiClient } from "@/lib/api";

export const workspaceService = {
  /**
   * List all workspaces
   */
  async listWorkspaces(params = {}) {
    return apiClient("/workspaces", { params });
  },

  /**
   * Get single workspace by ID
   */
  async getWorkspace(workspaceId) {
    return apiClient(`/workspaces/${workspaceId}`);
  },

  /**
   * Create a new workspace
   */
  async createWorkspace(payload) {
    return apiClient("/workspaces", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Update workspace details
   */
  async updateWorkspace(workspaceId, payload) {
    return apiClient(`/workspaces/${workspaceId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Delete a workspace
   */
  async deleteWorkspace(workspaceId) {
    return apiClient(`/workspaces/${workspaceId}`, {
      method: "DELETE",
    });
  },

  /**
   * List projects under a specific workspace
   */
  async listWorkspaceProjects(workspaceId, params = {}) {
    return apiClient(`/workspaces/${workspaceId}/projects`, { params });
  },

  /**
   * Create a project under a specific workspace
   */
  async createWorkspaceProject(workspaceId, payload) {
    return apiClient(`/workspaces/${workspaceId}/projects`, {
      method: "POST",
      body: payload,
    });
  },
};

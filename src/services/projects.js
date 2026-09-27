import { apiClient } from "@/lib/api";

export const projectService = {
  /**
   * List all projects across the platform
   */
  async listProjects(params = {}) {
    return apiClient("/projects", { params });
  },

  /**
   * Get single project by ID
   */
  async getProject(projectId) {
    return apiClient(`/projects/${projectId}`);
  },

  /**
   * Update project details
   */
  async updateProject(projectId, payload) {
    return apiClient(`/projects/${projectId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Delete a project
   */
  async deleteProject(projectId) {
    return apiClient(`/projects/${projectId}`, {
      method: "DELETE",
    });
  },

  /**
   * List tasks for a specific project
   */
  async listProjectTasks(projectId, params = {}) {
    return apiClient(`/projects/${projectId}/tasks`, { params });
  },

  /**
   * Create a task under a specific project
   */
  async createProjectTask(projectId, payload) {
    return apiClient(`/projects/${projectId}/tasks`, {
      method: "POST",
      body: payload,
    });
  },
};

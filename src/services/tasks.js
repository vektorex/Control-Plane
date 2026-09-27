import { apiClient } from "@/lib/api";

export const taskService = {
  /**
   * List all tasks across the platform
   */
  async listTasks(params = {}) {
    return apiClient("/tasks", { params });
  },

  /**
   * Get single task by ID
   */
  async getTask(taskId) {
    return apiClient(`/tasks/${taskId}`);
  },

  /**
   * Update task details (title, description, status)
   */
  async updateTask(taskId, payload) {
    return apiClient(`/tasks/${taskId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Delete a task
   */
  async deleteTask(taskId) {
    return apiClient(`/tasks/${taskId}`, {
      method: "DELETE",
    });
  },

  /**
   * List runs belonging to a task
   */
  async listTaskRuns(taskId, params = {}) {
    return apiClient(`/tasks/${taskId}/runs`, { params });
  },

  /**
   * Create an execution run under a task
   */
  async createTaskRun(taskId, payload) {
    return apiClient(`/tasks/${taskId}/runs`, {
      method: "POST",
      body: payload,
    });
  },
};

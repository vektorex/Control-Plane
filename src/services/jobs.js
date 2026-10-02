import { apiClient } from "@/lib/api";

export const jobService = {
  /**
   * List jobs in the workspace with optional status, type, and pagination filters
   */
  async listJobs(workspaceId, filters = {}) {
    const params = {
      ...(workspaceId ? { workspace_id: workspaceId } : {}),
      ...(filters.status && filters.status !== "all" ? { status: filters.status } : {}),
      ...(filters.jobType && filters.jobType !== "all" ? { job_type: filters.jobType } : {}),
      ...(filters.projectId ? { project_id: filters.projectId } : {}),
      ...(filters.parentJobId ? { parent_job_id: filters.parentJobId } : {}),
      ...(filters.limit ? { limit: filters.limit } : {}),
      ...(filters.offset !== undefined ? { offset: filters.offset } : {}),
    };
    return apiClient("/jobs", { params });
  },

  /**
   * Get single job details by ID
   */
  async getJob(jobId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/jobs/${jobId}`, { params });
  },

  /**
   * Enqueue a new durable background job
   */
  async createJob(workspaceId, payload) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient("/jobs", {
      method: "POST",
      params,
      body: payload,
    });
  },

  /**
   * Request cooperative cancellation of a queued or running job
   */
  async cancelJob(jobId, workspaceId, reason = null) {
    const params = {
      ...(workspaceId ? { workspace_id: workspaceId } : {}),
      ...(reason ? { reason } : {}),
    };
    return apiClient(`/jobs/${jobId}/cancel`, {
      method: "POST",
      params,
    });
  },

  /**
   * Manually retry an eligible failed or cancelled job
   */
  async retryJob(jobId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/jobs/${jobId}/retry`, {
      method: "POST",
      params,
    });
  },

  /**
   * Retrieve the audit event timeline for a job
   */
  async getJobEvents(jobId, workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient(`/jobs/${jobId}/events`, { params });
  },

  /**
   * Retrieve operational stats and queue health metrics
   */
  async getJobStats(workspaceId) {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    return apiClient("/jobs/operations/stats", { params });
  },
};

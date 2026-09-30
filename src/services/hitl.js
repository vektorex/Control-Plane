import { apiClient } from "@/lib/api";

/**
 * Service methods for Human-in-the-Loop (HITL) System (Step 18).
 */
export const hitlService = {
  /**
   * List intervention requests with optional filters (status, assigned_to, project_id, priority).
   */
  async listRequests(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.assigned_to) query.set("assigned_to", params.assigned_to);
    if (params.project_id) query.set("project_id", params.project_id);
    if (params.priority) query.set("priority", params.priority);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));
    const queryString = query.toString() ? `?${query.toString()}` : "";
    return apiClient(`/hitl/requests${queryString}`);
  },

  /**
   * Retrieve a single intervention request by ID.
   */
  async getRequest(requestId) {
    return apiClient(`/hitl/requests/${requestId}`);
  },

  /**
   * Approve an intervention request.
   */
  async approveRequest(requestId, comment = null) {
    return apiClient(`/hitl/requests/${requestId}/approve`, {
      method: "POST",
      body: { comment },
    });
  },

  /**
   * Reject an intervention request.
   */
  async rejectRequest(requestId, comment = null) {
    return apiClient(`/hitl/requests/${requestId}/reject`, {
      method: "POST",
      body: { comment },
    });
  },

  /**
   * Edit input payload and approve with edited data.
   */
  async editRequest(requestId, editedData, comment = null) {
    return apiClient(`/hitl/requests/${requestId}/edit`, {
      method: "POST",
      body: { edited_data: editedData, comment },
    });
  },

  /**
   * Cancel an intervention request.
   */
  async cancelRequest(requestId, comment = null) {
    return apiClient(`/hitl/requests/${requestId}/cancel`, {
      method: "POST",
      body: { comment },
    });
  },

  /**
   * Assign an intervention request to a specific user.
   */
  async assignRequest(requestId, assignedTo) {
    return apiClient(`/hitl/requests/${requestId}/assign`, {
      method: "POST",
      body: { assigned_to: assignedTo },
    });
  },

  /**
   * Get workspace approval policies.
   */
  async getPolicies() {
    return apiClient("/hitl/policies");
  },

  /**
   * Update workspace approval policies.
   */
  async updatePolicies(data) {
    return apiClient("/hitl/policies", {
      method: "PATCH",
      body: data,
    });
  },
};

import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 37: Public API & Developer Platform.
 */
export const developerService = {
  /**
   * Fetch developer platform overview statistics.
   */
  async getOverview() {
    return apiClient("/developer/overview");
  },

  /**
   * List developer applications.
   */
  async listApplications(params = {}) {
    const q = new URLSearchParams();
    if (params.environment) q.set("environment", params.environment);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/developer/applications${qs ? `?${qs}` : ""}`);
  },

  /**
   * Create developer application.
   */
  async createApplication(data) {
    return apiClient("/developer/applications", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get application detail.
   */
  async getApplication(id) {
    return apiClient(`/developer/applications/${id}`);
  },

  /**
   * Update application.
   */
  async updateApplication(id, data) {
    return apiClient(`/developer/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Delete application.
   */
  async deleteApplication(id) {
    return apiClient(`/developer/applications/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * List credentials for an application.
   */
  async listCredentials(applicationId) {
    return apiClient(`/developer/applications/${applicationId}/credentials`);
  },

  /**
   * Create scoped API credential. (Returns secret_key ONLY ONCE).
   */
  async createCredential(applicationId, data) {
    return apiClient(`/developer/applications/${applicationId}/credentials`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Rotate credential. (Returns new secret_key ONLY ONCE).
   */
  async rotateCredential(credentialId, data = {}) {
    return apiClient(`/developer/credentials/${credentialId}/rotate`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Revoke credential.
   */
  async revokeCredential(credentialId) {
    return apiClient(`/developer/credentials/${credentialId}/revoke`, {
      method: "POST",
    });
  },

  /**
   * List webhooks for an application.
   */
  async listWebhooks(applicationId) {
    return apiClient(`/developer/applications/${applicationId}/webhooks`);
  },

  /**
   * Create webhook subscription. (Returns webhook_secret ONLY ONCE).
   */
  async createWebhook(applicationId, data) {
    return apiClient(`/developer/applications/${applicationId}/webhooks`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Update webhook subscription.
   */
  async updateWebhook(webhookId, data) {
    return apiClient(`/developer/webhooks/${webhookId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Delete webhook subscription.
   */
  async deleteWebhook(webhookId) {
    return apiClient(`/developer/webhooks/${webhookId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get application usage telemetry.
   */
  async getApplicationUsage(applicationId, params = {}) {
    const q = new URLSearchParams();
    if (params.periodHours) q.set("period_hours", params.periodHours);
    const qs = q.toString();
    return apiClient(`/developer/applications/${applicationId}/usage${qs ? `?${qs}` : ""}`);
  },

  /**
   * List quotas for an application.
   */
  async listQuotas(applicationId) {
    return apiClient(`/developer/quotas?application_id=${applicationId}`);
  },

  /**
   * Set quota on an application.
   */
  async createQuota(applicationId, data) {
    return apiClient(`/developer/quotas?application_id=${applicationId}`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List production approvals.
   */
  async listApprovals(params = {}) {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    const qs = q.toString();
    return apiClient(`/developer/approvals${qs ? `?${qs}` : ""}`);
  },

  /**
   * Review production approval request.
   */
  async reviewApproval(approvalId, data) {
    return apiClient(`/developer/approvals/${approvalId}/review`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Fetch public OpenAPI 3.0 specification.
   */
  async getPublicOpenApiSpec() {
    return apiClient("/developer/openapi.json");
  },

  /**
   * Safe sandbox / API explorer execution.
   */
  async executePublicSandbox(method, path, headers = {}, body = null) {
    const url = path.startsWith("/api/v1") ? path : `/v1${path.startsWith("/") ? path : `/${path}`}`;
    const opts = {
      method,
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
    };
    if (body && method.toUpperCase() !== "GET") {
      opts.body = typeof body === "string" ? body : JSON.stringify(body);
    }
    return apiClient(url, opts);
  },
};

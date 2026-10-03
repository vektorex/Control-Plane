import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 32: AI Governance, Policy Control Plane, and Safety Guardrails.
 */
export const governanceService = {
  /**
   * Fetch aggregate governance metrics, enforcement rates, and budget status.
   */
  async getStats(workspaceId) {
    return apiClient("/governance/stats", {
      params: { workspace_id: workspaceId },
    });
  },

  /**
   * List governance policies filtered by workspace, project, scope, and status.
   */
  async listPolicies({ workspaceId, projectId, scope, status } = {}) {
    return apiClient("/governance/policies", {
      params: {
        workspace_id: workspaceId,
        project_id: projectId,
        scope,
        status,
      },
    });
  },

  /**
   * Fetch a single governance policy by ID.
   */
  async getPolicy(policyId) {
    return apiClient(`/governance/policies/${policyId}`);
  },

  /**
   * Create a new governance policy (Admin only).
   */
  async createPolicy(data) {
    return apiClient("/governance/policies", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Update policy metadata (name, description, tags, fail_safe_mode).
   */
  async updatePolicy(policyId, data) {
    return apiClient(`/governance/policies/${policyId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Soft-delete/archive a governance policy.
   */
  async deletePolicy(policyId) {
    return apiClient(`/governance/policies/${policyId}`, {
      method: "DELETE",
    });
  },

  /**
   * Create a new draft version for a policy.
   */
  async createVersion(policyId, data) {
    return apiClient(`/governance/policies/${policyId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * List versions of a policy.
   */
  async listVersions(policyId) {
    return apiClient(`/governance/policies/${policyId}/versions`);
  },

  /**
   * Activate a draft version of a policy.
   */
  async activateVersion(policyId, versionId) {
    return apiClient(`/governance/policies/${policyId}/versions/${versionId}/activate`, {
      method: "POST",
    });
  },

  /**
   * Evaluate governance for an execution context.
   */
  async evaluate(data) {
    return apiClient("/governance/evaluate", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Simulate a request against active policies without side effects.
   */
  async simulate(data) {
    return apiClient("/governance/simulate", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Preview a hypothetical policy configuration against an evaluation request.
   */
  async preview(data) {
    return apiClient("/governance/preview", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Create or update budget policy.
   */
  async upsertBudget(data) {
    return apiClient("/governance/budgets", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * Get active budget policy.
   */
  async getBudget({ workspaceId, projectId } = {}) {
    return apiClient("/governance/budgets", {
      params: {
        workspace_id: workspaceId,
        project_id: projectId,
      },
    });
  },

  /**
   * Classify an artifact, document, connector, or memory entity.
   */
  async classify(data) {
    return apiClient("/governance/classify", {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  },

  /**
   * List immutable governance decision logs.
   */
  async listDecisions({ workspaceId, enforcementPoint, decision, limit = 50 } = {}) {
    return apiClient("/governance/decisions", {
      params: {
        workspace_id: workspaceId,
        enforcement_point: enforcementPoint,
        decision,
        limit,
      },
    });
  },
};

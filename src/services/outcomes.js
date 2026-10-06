import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 43: AI Outcome Intelligence & Work Impact Layer.
 */
export const outcomeService = {
  // ===========================================================================
  // Objectives
  // ===========================================================================

  async listObjectives(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.status) q.set("status", params.status);
    if (params.objectiveType) q.set("objective_type", params.objectiveType);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/objectives${qs ? `?${qs}` : ""}`);
  },

  async getObjective(objectiveId) {
    return apiClient(`/objectives/${objectiveId}`);
  },

  async createObjective(data) {
    return apiClient("/objectives", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateObjective(objectiveId, data) {
    return apiClient(`/objectives/${objectiveId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async deleteObjective(objectiveId) {
    return apiClient(`/objectives/${objectiveId}`, {
      method: "DELETE",
    });
  },

  async getObjectiveHealth(objectiveId) {
    return apiClient(`/objectives/${objectiveId}/health`);
  },

  async getObjectiveWorkMap(objectiveId) {
    return apiClient(`/objectives/${objectiveId}/work-map`);
  },

  async getObjectiveRecommendations(objectiveId) {
    return apiClient(`/objectives/${objectiveId}/recommendations`);
  },

  // ===========================================================================
  // Targets & Milestones
  // ===========================================================================

  async createTarget(objectiveId, data) {
    return apiClient(`/objectives/${objectiveId}/targets`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listTargets(objectiveId) {
    return apiClient(`/objectives/${objectiveId}/targets`);
  },

  async updateTarget(targetId, data) {
    return apiClient(`/outcome-targets/${targetId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async createMilestone(objectiveId, data) {
    return apiClient(`/objectives/${objectiveId}/milestones`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listMilestones(objectiveId) {
    return apiClient(`/objectives/${objectiveId}/milestones`);
  },

  // ===========================================================================
  // Outcomes
  // ===========================================================================

  async listOutcomes(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.objectiveId) q.set("objective_id", params.objectiveId);
    if (params.status) q.set("status", params.status);
    if (params.outcomeType) q.set("outcome_type", params.outcomeType);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/outcomes${qs ? `?${qs}` : ""}`);
  },

  async getOutcome(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}`);
  },

  async createOutcome(data) {
    return apiClient("/outcomes", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateOutcome(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async deleteOutcome(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}`, {
      method: "DELETE",
    });
  },

  async addEvidence(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}/evidence`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listEvidence(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/evidence`);
  },

  async addMeasurement(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}/measurements`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listMeasurements(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/measurements`);
  },

  async addWorkLink(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}/work`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listWorkLinks(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/work`);
  },

  async verifyOutcome(outcomeId, data = {}) {
    return apiClient(`/outcomes/${outcomeId}/verify`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async disputeOutcome(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}/dispute`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async addAttribution(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}/attributions`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listAttributions(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/attributions`);
  },

  async addImpact(outcomeId, data) {
    return apiClient(`/outcomes/${outcomeId}/impact`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listImpact(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/impact`);
  },

  async getOutcomeHealth(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/health`);
  },

  async getOutcomeGraph(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/graph`);
  },

  async getOutcomeRecommendations(outcomeId) {
    return apiClient(`/outcomes/${outcomeId}/recommendations`);
  },

  // ===========================================================================
  // Decisions
  // ===========================================================================

  async listDecisions(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.objectiveId) q.set("objective_id", params.objectiveId);
    if (params.outcomeId) q.set("outcome_id", params.outcomeId);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/outcome-decisions${qs ? `?${qs}` : ""}`);
  },

  async getDecision(decisionId) {
    return apiClient(`/outcome-decisions/${decisionId}`);
  },

  async createDecision(data) {
    return apiClient("/outcome-decisions", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateDecision(decisionId, data) {
    return apiClient(`/outcome-decisions/${decisionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async approveDecision(decisionId) {
    return apiClient(`/outcome-decisions/${decisionId}/approve`, {
      method: "POST",
    });
  },

  async rejectDecision(decisionId, reason) {
    const q = reason ? `?reason=${encodeURIComponent(reason)}` : "";
    return apiClient(`/outcome-decisions/${decisionId}/reject${q}`, {
      method: "POST",
    });
  },
};

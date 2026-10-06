import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 44: AI Work Planning, Capacity & Resource Optimization Layer.
 */
export const planningService = {
  // ===========================================================================
  // Work Plans
  // ===========================================================================

  async listWorkPlans(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.objectiveId) q.set("objective_id", params.objectiveId);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/work-plans${qs ? `?${qs}` : ""}`);
  },

  async getWorkPlan(planId) {
    return apiClient(`/work-plans/${planId}`);
  },

  async createWorkPlan(data) {
    return apiClient("/work-plans", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateWorkPlan(planId, data) {
    return apiClient(`/work-plans/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async generatePlan(planId, data = {}) {
    return apiClient(`/work-plans/${planId}/plan`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async validatePlan(planId) {
    return apiClient(`/work-plans/${planId}/validate`, {
      method: "POST",
    });
  },

  async activatePlan(planId) {
    return apiClient(`/work-plans/${planId}/activate`, {
      method: "POST",
    });
  },

  async pausePlan(planId) {
    return apiClient(`/work-plans/${planId}/pause`, {
      method: "POST",
    });
  },

  async getPlanDependencies(planId) {
    return apiClient(`/work-plans/${planId}/dependencies`);
  },

  async getPlanResources(planId) {
    return apiClient(`/work-plans/${planId}/resources`);
  },

  async getPlanConflicts(planId) {
    return apiClient(`/work-plans/${planId}/conflicts`);
  },

  async getPlanBlockers(planId) {
    return apiClient(`/work-plans/${planId}/blockers`);
  },

  async addPlanItem(planId, data) {
    return apiClient(`/work-plans/${planId}/items`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async addPlanDependency(planId, data) {
    return apiClient(`/work-plans/${planId}/dependencies`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ===========================================================================
  // Resources & Capacity
  // ===========================================================================

  async listResources(params = {}) {
    const q = new URLSearchParams();
    if (params.resourceType) q.set("resource_type", params.resourceType);
    if (params.status) q.set("status", params.status);
    const qs = q.toString();
    return apiClient(`/resources${qs ? `?${qs}` : ""}`);
  },

  async getResource(resourceId) {
    return apiClient(`/resources/${resourceId}`);
  },

  async createResource(data) {
    return apiClient("/resources", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async getResourceCapacity(resourceId) {
    return apiClient(`/resources/${resourceId}/capacity`);
  },

  async addResourceAvailability(resourceId, data) {
    return apiClient(`/resources/${resourceId}/availability`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listReservations(resourceId = null) {
    const q = resourceId ? `?resource_id=${encodeURIComponent(resourceId)}` : "";
    return apiClient(`/reservations${q}`);
  },

  async createReservation(data) {
    return apiClient("/reservations", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async getCapacityForecast(horizonDays = 14) {
    return apiClient(`/planning/forecast?horizon_days=${horizonDays}`);
  },

  async getCapacityWorkload() {
    return apiClient("/planning/workload");
  },

  async listRecommendations(workPlanId = null) {
    const q = workPlanId ? `?work_plan_id=${encodeURIComponent(workPlanId)}` : "";
    return apiClient(`/planning/recommendations${q}`);
  },

  // ===========================================================================
  // Scenarios
  // ===========================================================================

  async createScenario(data) {
    return apiClient("/planning-scenarios", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async getScenario(scenarioId) {
    return apiClient(`/planning-scenarios/${scenarioId}`);
  },

  async runScenario(scenarioId) {
    return apiClient(`/planning-scenarios/${scenarioId}/run`, {
      method: "POST",
    });
  },
};

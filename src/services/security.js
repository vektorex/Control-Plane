import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 34: AI Security Operations, Threat Detection & Incident Response Layer.
 */
export const securityService = {
  /**
   * Fetch security overview metrics and active counts.
   */
  async getOverview({ workspaceId, projectId } = {}) {
    return apiClient("/security/overview", {
      params: {
        workspace_id: workspaceId,
        project_id: projectId,
      },
    });
  },

  /**
   * List detected security signals with filtering.
   */
  async listSignals(params = {}) {
    return apiClient("/security/signals", {
      params: {
        workspace_id: params.workspaceId,
        project_id: params.projectId,
        signal_type: params.signalType,
        source_type: params.sourceType,
        severity: params.severity,
        status: params.status,
        actor_id: params.actorId,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Get single signal by ID.
   */
  async getSignal(signalId) {
    return apiClient(`/security/signals/${signalId}`);
  },

  /**
   * Update signal status (e.g. dismiss or mark triaged).
   */
  async updateSignal(signalId, data) {
    return apiClient(`/security/signals/${signalId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List security incidents with filtering.
   */
  async listIncidents(params = {}) {
    return apiClient("/security/incidents", {
      params: {
        workspace_id: params.workspaceId,
        project_id: params.projectId,
        status: params.status,
        severity: params.severity,
        category: params.category,
        assigned_to: params.assignedTo,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Create a new security incident manually.
   */
  async createIncident(data) {
    return apiClient("/security/incidents", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get single incident by ID.
   */
  async getIncident(incidentId) {
    return apiClient(`/security/incidents/${incidentId}`);
  },

  /**
   * Update incident (assign, change status, resolve).
   */
  async updateIncident(incidentId, data) {
    return apiClient(`/security/incidents/${incidentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Fetch append-only chronological timeline for an incident.
   */
  async getIncidentTimeline(incidentId) {
    return apiClient(`/security/incidents/${incidentId}/timeline`);
  },

  /**
   * List correlated signals for an incident.
   */
  async getIncidentSignals(incidentId) {
    return apiClient(`/security/incidents/${incidentId}/signals`);
  },

  /**
   * Fetch bounded investigation graph context.
   */
  async getIncidentInvestigation(incidentId) {
    return apiClient(`/security/incidents/${incidentId}/investigation`);
  },

  /**
   * Fetch immutable compliance evidence records linked to this incident.
   */
  async getIncidentEvidence(incidentId) {
    return apiClient(`/security/incidents/${incidentId}/evidence`);
  },

  /**
   * Request a containment action for an incident.
   */
  async requestContainment(incidentId, data) {
    return apiClient(`/security/incidents/${incidentId}/containment`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List containment actions associated with an incident.
   */
  async listContainmentActions(incidentId) {
    return apiClient(`/security/incidents/${incidentId}/containment`);
  },

  /**
   * Execute or approve an authorized containment action.
   */
  async executeContainment(incidentId, actionId, data = {}) {
    return apiClient(`/security/incidents/${incidentId}/containment/${actionId}/execute`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List threat indicators / fingerprints.
   */
  async listIndicators(params = {}) {
    return apiClient("/security/indicators", {
      params: {
        indicator_type: params.indicatorType,
        status: params.status,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * List response playbooks.
   */
  async listPlaybooks(params = {}) {
    return apiClient("/security/playbooks", {
      params: {
        enabled: params.enabled,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Create response playbook.
   */
  async createPlaybook(data) {
    return apiClient("/security/playbooks", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Update response playbook.
   */
  async updatePlaybook(id, data) {
    return apiClient(`/security/playbooks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Delete response playbook.
   */
  async deletePlaybook(id) {
    return apiClient(`/security/playbooks/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * Dry-run test a response playbook against sample signal criteria.
   */
  async testPlaybook(id, signalData) {
    return apiClient(`/security/playbooks/${id}/test`, {
      method: "POST",
      body: JSON.stringify(signalData),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List deterministic detectors registered in the engine.
   */
  async listDetectors() {
    return apiClient("/security/detections");
  },

  /**
   * Get historical security statistics.
   */
  async getStatistics(params = {}) {
    return apiClient("/security/statistics", {
      params: {
        days: params.days || 30,
        workspace_id: params.workspaceId,
        project_id: params.projectId,
      },
    });
  },
};

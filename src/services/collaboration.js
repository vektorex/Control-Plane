import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 39: Multi-User Collaboration, Shared AI Workspaces & Real-Time Co-Execution.
 *
 * NOTE: Collaboration provides shared application state and realtime coordination.
 * It does not replace authorization, governance, human approval, or the underlying execution systems.
 */
export const collaborationService = {
  // ---------------------------------------------------------------------------
  // Sessions
  // ---------------------------------------------------------------------------

  async listSessions(params = {}) {
    const q = new URLSearchParams();
    if (params.workspaceId) q.set("workspace_id", params.workspaceId);
    if (params.resourceType) q.set("resource_type", params.resourceType);
    if (params.resourceId) q.set("resource_id", params.resourceId);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/collaboration/sessions${qs ? `?${qs}` : ""}`);
  },

  async createSession(data) {
    return apiClient("/collaboration/sessions", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async getSession(sessionId) {
    return apiClient(`/collaboration/sessions/${sessionId}`);
  },

  async updateSession(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async closeSession(sessionId) {
    return apiClient(`/collaboration/sessions/${sessionId}/close`, {
      method: "POST",
    });
  },

  // ---------------------------------------------------------------------------
  // Participants & Presence
  // ---------------------------------------------------------------------------

  async joinSession(sessionId, role = "editor") {
    return apiClient(`/collaboration/sessions/${sessionId}/join`, {
      method: "POST",
      body: JSON.stringify({ role }),
      headers: { "Content-Type": "application/json" },
    });
  },

  async recordHeartbeat(sessionId, data = {}) {
    return apiClient(`/collaboration/sessions/${sessionId}/heartbeat`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async leaveSession(sessionId) {
    return apiClient(`/collaboration/sessions/${sessionId}/leave`, {
      method: "POST",
    });
  },

  async listParticipants(sessionId) {
    return apiClient(`/collaboration/sessions/${sessionId}/participants`);
  },

  // ---------------------------------------------------------------------------
  // Activity Feed
  // ---------------------------------------------------------------------------

  async listActivity(sessionId, params = {}) {
    const q = new URLSearchParams();
    if (params.activityType) q.set("activity_type", params.activityType);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/collaboration/sessions/${sessionId}/activity${qs ? `?${qs}` : ""}`);
  },

  // ---------------------------------------------------------------------------
  // Comments & Mentions
  // ---------------------------------------------------------------------------

  async listComments(sessionId, params = {}) {
    const q = new URLSearchParams();
    if (params.resourceType) q.set("resource_type", params.resourceType);
    if (params.resourceId) q.set("resource_id", params.resourceId);
    if (params.includeDeleted) q.set("include_deleted", params.includeDeleted);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/collaboration/sessions/${sessionId}/comments${qs ? `?${qs}` : ""}`);
  },

  async addComment(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/comments`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateComment(commentId, data) {
    return apiClient(`/collaboration/comments/${commentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async deleteComment(commentId) {
    return apiClient(`/collaboration/comments/${commentId}`, {
      method: "DELETE",
    });
  },

  // ---------------------------------------------------------------------------
  // Assignments
  // ---------------------------------------------------------------------------

  async listAssignments(sessionId, params = {}) {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    if (params.assignedTo) q.set("assigned_to", params.assignedTo);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/collaboration/sessions/${sessionId}/assignments${qs ? `?${qs}` : ""}`);
  },

  async createAssignment(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/assignments`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateAssignment(assignmentId, data) {
    return apiClient(`/collaboration/assignments/${assignmentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ---------------------------------------------------------------------------
  // Annotations
  // ---------------------------------------------------------------------------

  async listAnnotations(sessionId, params = {}) {
    const q = new URLSearchParams();
    if (params.resourceType) q.set("resource_type", params.resourceType);
    if (params.resourceId) q.set("resource_id", params.resourceId);
    if (params.annotationType) q.set("annotation_type", params.annotationType);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/collaboration/sessions/${sessionId}/annotations${qs ? `?${qs}` : ""}`);
  },

  async createAnnotation(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/annotations`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateAnnotation(annotationId, data) {
    return apiClient(`/collaboration/annotations/${annotationId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ---------------------------------------------------------------------------
  // Shared Decisions
  // ---------------------------------------------------------------------------

  async listDecisions(sessionId, limit = 50) {
    return apiClient(`/collaboration/sessions/${sessionId}/decisions?limit=${limit}`);
  },

  async recordDecision(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/decisions`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ---------------------------------------------------------------------------
  // AI Co-Execution
  // ---------------------------------------------------------------------------

  async initiateRun(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/run`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async pauseRun(runId) {
    return apiClient(`/collaboration/runs/${runId}/pause`, {
      method: "POST",
    });
  },

  async resumeRun(runId) {
    return apiClient(`/collaboration/runs/${runId}/resume`, {
      method: "POST",
    });
  },

  async cancelRun(runId) {
    return apiClient(`/collaboration/runs/${runId}/cancel`, {
      method: "POST",
    });
  },

  // ---------------------------------------------------------------------------
  // Collaborative State & Advisory Locks
  // ---------------------------------------------------------------------------

  async getState(sessionId, resourceType, resourceId) {
    const q = new URLSearchParams({ resource_type: resourceType, resource_id: resourceId });
    return apiClient(`/collaboration/sessions/${sessionId}/state?${q.toString()}`);
  },

  async updateState(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/state`, {
      method: "PUT",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async acquireLock(sessionId, data) {
    return apiClient(`/collaboration/sessions/${sessionId}/lock`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async releaseLock(sessionId, resourceType, resourceId) {
    const q = new URLSearchParams({ resource_type: resourceType, resource_id: resourceId });
    return apiClient(`/collaboration/sessions/${sessionId}/lock?${q.toString()}`, {
      method: "DELETE",
    });
  },

  async getWorkspaceSummary(workspaceId, resourceType, resourceId) {
    const q = new URLSearchParams({
      workspace_id: workspaceId,
      resource_type: resourceType,
      resource_id: resourceId,
    });
    return apiClient(`/collaboration/workspace/summary?${q.toString()}`);
  },

  // ---------------------------------------------------------------------------
  // Real-Time SSE Event Stream
  // ---------------------------------------------------------------------------

  subscribeEvents(sessionId, onEvent, onError) {
    if (typeof window === "undefined" || !window.EventSource) {
      return () => {};
    }

    const token = typeof localStorage !== "undefined" ? localStorage.getItem("auth_token") : null;
    const url = `/api/collaboration/sessions/${sessionId}/events${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    const es = new EventSource(url);

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (onEvent) onEvent(payload);
      } catch {
        if (onEvent) onEvent(event.data);
      }
    };

    es.onerror = (err) => {
      if (onError) onError(err);
    };

    return () => {
      es.close();
    };
  },
};

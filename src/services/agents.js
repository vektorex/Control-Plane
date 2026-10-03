import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 40: Governed AI Agent Runtime and Multi-Agent Teams.
 */
export const agentService = {
  // ---------------------------------------------------------------------------
  // Agents CRUD & Lifecycle
  // ---------------------------------------------------------------------------

  async listAgents(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/agents${qs ? `?${qs}` : ""}`);
  },

  async getAgent(agentId) {
    return apiClient(`/agents/${agentId}`);
  },

  async createAgent(data) {
    return apiClient("/agents", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateAgent(agentId, data) {
    return apiClient(`/agents/${agentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async deleteAgent(agentId) {
    return apiClient(`/agents/${agentId}`, {
      method: "DELETE",
    });
  },

  async createAgentVersion(agentId, data) {
    return apiClient(`/agents/${agentId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listAgentVersions(agentId) {
    return apiClient(`/agents/${agentId}/versions`);
  },

  async publishAgentVersion(agentId, versionId = null) {
    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return apiClient(`/agents/${agentId}/publish${query}`, {
      method: "POST",
    });
  },

  async activateAgent(agentId) {
    return apiClient(`/agents/${agentId}/activate`, {
      method: "POST",
    });
  },

  async pauseAgent(agentId) {
    return apiClient(`/agents/${agentId}/pause`, {
      method: "POST",
    });
  },

  async previewAgentPolicy(agentId, versionId = null) {
    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return apiClient(`/agents/${agentId}/preview${query}`);
  },

  // ---------------------------------------------------------------------------
  // Agent Runs & Delegations
  // ---------------------------------------------------------------------------

  async runAgent(agentId, data = {}) {
    return apiClient(`/agents/${agentId}/runs`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listAgentRuns(agentId, params = {}) {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/agents/${agentId}/runs${qs ? `?${qs}` : ""}`);
  },

  async getAgentRun(runId) {
    return apiClient(`/agent-runs/${runId}`);
  },

  async getAgentRunTrace(runId) {
    return apiClient(`/agent-runs/${runId}/trace`);
  },

  async replayAgentRun(runId) {
    return apiClient(`/agent-runs/${runId}/replay`);
  },

  async delegateAgent(agentId, data) {
    return apiClient(`/agents/${agentId}/delegate`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  // ---------------------------------------------------------------------------
  // Multi-Agent Teams
  // ---------------------------------------------------------------------------

  async listTeams(params = {}) {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/agent-teams${qs ? `?${qs}` : ""}`);
  },

  async getTeam(teamId) {
    return apiClient(`/agent-teams/${teamId}`);
  },

  async createTeam(data) {
    return apiClient("/agent-teams", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateTeam(teamId, data) {
    return apiClient(`/agent-teams/${teamId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async activateTeam(teamId) {
    return apiClient(`/agent-teams/${teamId}/activate`, {
      method: "POST",
    });
  },

  async pauseTeam(teamId) {
    return apiClient(`/agent-teams/${teamId}/pause`, {
      method: "POST",
    });
  },

  async runTeam(teamId, data = {}) {
    return apiClient(`/agent-teams/${teamId}/runs`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async listTeamRuns(teamId, params = {}) {
    const q = new URLSearchParams();
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/agent-teams/${teamId}/runs${qs ? `?${qs}` : ""}`);
  },

  async getTeamRun(runId) {
    return apiClient(`/agent-team-runs/${runId}`);
  },

  async resolveConflict(runId, conflictId, data) {
    return apiClient(`/agent-team-runs/${runId}/conflicts/${conflictId}/resolve`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },
};

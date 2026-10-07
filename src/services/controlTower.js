import { apiClient } from "@/lib/api";

export const controlTowerService = {
  getOverview: async (workspaceId) => {
    return apiClient("/control-tower/overview", {
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
  getAttention: async (workspaceId) => {
    return apiClient("/control-tower/attention", {
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
  acknowledgeAttention: async (attentionId, userId, workspaceId) => {
    return apiClient(`/control-tower/attention/${attentionId}/acknowledge`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
  search: async (query, workspaceId) => {
    return apiClient("/control-tower/search", {
      params: { q: query },
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
  generateBriefing: async (mode = "brief", workspaceId) => {
    return apiClient("/control-tower/briefing", {
      method: "POST",
      body: JSON.stringify({ mode }),
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
  getViews: async (workspaceId) => {
    return apiClient("/control-tower/views", {
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
  createView: async (viewData, workspaceId) => {
    return apiClient("/control-tower/views", {
      method: "POST",
      body: JSON.stringify(viewData),
      headers: { "X-Workspace-Id": workspaceId }
    });
  },
};

import { apiClient } from "@/lib/api";

export const organizationService = {
  /**
   * List organizations user belongs to
   */
  async listOrganizations() {
    return apiClient("/organizations");
  },

  /**
   * Create a new organization
   */
  async createOrganization(payload) {
    return apiClient("/organizations", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Get single organization by ID
   */
  async getOrganization(orgId) {
    return apiClient(`/organizations/${orgId}`);
  },

  /**
   * Update organization details
   */
  async updateOrganization(orgId, payload) {
    return apiClient(`/organizations/${orgId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Archive / soft-delete organization
   */
  async deleteOrganization(orgId) {
    return apiClient(`/organizations/${orgId}`, {
      method: "DELETE",
    });
  },

  /**
   * List organization members
   */
  async listMembers(orgId) {
    return apiClient(`/organizations/${orgId}/members`);
  },

  /**
   * Update member role or status
   */
  async updateMember(orgId, memberId, payload) {
    return apiClient(`/organizations/${orgId}/members/${memberId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Remove member from organization
   */
  async removeMember(orgId, memberId) {
    return apiClient(`/organizations/${orgId}/members/${memberId}`, {
      method: "DELETE",
    });
  },

  /**
   * Transfer organization ownership
   */
  async transferOwnership(orgId, targetUserId) {
    return apiClient(`/organizations/${orgId}/transfer-ownership`, {
      method: "POST",
      body: { target_user_id: targetUserId },
    });
  },

  /**
   * List organization invitations
   */
  async listInvitations(orgId) {
    return apiClient(`/organizations/${orgId}/invitations`);
  },

  /**
   * Send an invitation
   */
  async createInvitation(orgId, payload) {
    return apiClient(`/organizations/${orgId}/invitations`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Revoke an invitation
   */
  async revokeInvitation(orgId, invitationId) {
    return apiClient(`/organizations/${orgId}/invitations/${invitationId}`, {
      method: "DELETE",
    });
  },

  /**
   * Accept an invitation token
   */
  async acceptInvitation(token) {
    return apiClient(`/invitations/${token}/accept`, {
      method: "POST",
    });
  },

  /**
   * List organization workspaces
   */
  async listWorkspaces(orgId) {
    return apiClient(`/organizations/${orgId}/workspaces`);
  },

  /**
   * Create workspace within an organization
   */
  async createWorkspace(orgId, payload) {
    return apiClient(`/organizations/${orgId}/workspaces`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Workspace Member management
   */
  async listWorkspaceMembers(workspaceId) {
    return apiClient(`/workspaces/${workspaceId}/members`);
  },

  async updateWorkspaceMember(workspaceId, memberId, payload) {
    return apiClient(`/workspaces/${workspaceId}/members/${memberId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async removeWorkspaceMember(workspaceId, memberId) {
    return apiClient(`/workspaces/${workspaceId}/members/${memberId}`, {
      method: "DELETE",
    });
  },

  /**
   * Project Access management
   */
  async listProjectMembers(projectId) {
    return apiClient(`/projects/${projectId}/members`);
  },

  async addProjectMember(projectId, payload) {
    return apiClient(`/projects/${projectId}/members`, {
      method: "POST",
      body: payload,
    });
  },

  async updateProjectMember(projectId, memberId, payload) {
    return apiClient(`/projects/${projectId}/members/${memberId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  async removeProjectMember(projectId, memberId) {
    return apiClient(`/projects/${projectId}/members/${memberId}`, {
      method: "DELETE",
    });
  },
};

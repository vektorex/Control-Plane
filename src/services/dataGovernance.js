import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 33: Data Governance, Privacy & Compliance Evidence Layer.
 */
export const dataGovernanceService = {
  /**
   * Fetch aggregate governance overview metrics, counts, and chain status.
   */
  async getOverview({ workspaceId } = {}) {
    return apiClient("/data-governance/overview", {
      params: { workspace_id: workspaceId },
    });
  },

  /**
   * List logical data assets with filtering.
   */
  async listAssets(params = {}) {
    return apiClient("/data-governance/assets", {
      params: {
        workspace_id: params.workspaceId,
        project_id: params.projectId,
        asset_type: params.assetType,
        resource_type: params.resourceType,
        classification: params.classification,
        status: params.status,
        contains_secrets: params.containsSecrets,
        contains_personal_data: params.containsPersonalData,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Get single asset by ID.
   */
  async getAsset(assetId) {
    return apiClient(`/data-governance/assets/${assetId}`);
  },

  /**
   * Register a new logical asset.
   */
  async registerAsset(data) {
    return apiClient("/data-governance/assets", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Update asset metadata.
   */
  async updateAsset(assetId, data) {
    return apiClient(`/data-governance/assets/${assetId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get bounded lineage subgraph for an asset.
   */
  async getAssetLineage(assetId, { depth = 3, direction = "both" } = {}) {
    return apiClient(`/data-governance/assets/${assetId}/lineage`, {
      params: { depth, direction },
    });
  },

  /**
   * Record a directed lineage edge.
   */
  async createLineageEdge(data) {
    return apiClient("/data-governance/lineage", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get access history logs for an asset.
   */
  async getAssetAccessHistory(assetId, { limit = 50, offset = 0 } = {}) {
    return apiClient(`/data-governance/assets/${assetId}/access-history`, {
      params: { limit, offset },
    });
  },

  /**
   * List classification records.
   */
  async listClassifications(params = {}) {
    return apiClient("/data-governance/classifications", {
      params: {
        workspace_id: params.workspaceId,
        asset_id: params.assetId,
        classification: params.classification,
      },
    });
  },

  /**
   * Authoritative classification review / manual transition.
   */
  async reviewClassification(data) {
    return apiClient("/data-governance/classifications/review", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Retention Policies.
   */
  async listRetentionPolicies(params = {}) {
    return apiClient("/data-governance/retention-policies", {
      params: {
        workspace_id: params.workspaceId,
        resource_type: params.resourceType,
        enabled: params.enabled,
      },
    });
  },

  async createRetentionPolicy(data) {
    return apiClient("/data-governance/retention-policies", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updateRetentionPolicy(id, data) {
    return apiClient(`/data-governance/retention-policies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async deleteRetentionPolicy(id) {
    return apiClient(`/data-governance/retention-policies/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * Privacy Requests.
   */
  async listPrivacyRequests(params = {}) {
    return apiClient("/data-governance/privacy-requests", {
      params: {
        workspace_id: params.workspaceId,
        status: params.status,
        request_type: params.requestType,
      },
    });
  },

  async getPrivacyRequest(id) {
    return apiClient(`/data-governance/privacy-requests/${id}`);
  },

  async createPrivacyRequest(data) {
    return apiClient("/data-governance/privacy-requests", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async updatePrivacyRequest(id, data) {
    return apiClient(`/data-governance/privacy-requests/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Data Exports.
   */
  async listExports(params = {}) {
    return apiClient("/data-governance/exports", {
      params: {
        workspace_id: params.workspaceId,
        status: params.status,
      },
    });
  },

  async getExport(id) {
    return apiClient(`/data-governance/exports/${id}`);
  },

  async createExport(data) {
    return apiClient("/data-governance/exports", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Safe Deletion Requests.
   */
  async listDeletions(params = {}) {
    return apiClient("/data-governance/deletions", {
      params: {
        workspace_id: params.workspaceId,
        status: params.status,
      },
    });
  },

  async getDeletion(id) {
    return apiClient(`/data-governance/deletions/${id}`);
  },

  async createDeletion(data) {
    return apiClient("/data-governance/deletions", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Legal Holds.
   */
  async listLegalHolds(params = {}) {
    return apiClient("/data-governance/legal-holds", {
      params: {
        workspace_id: params.workspaceId,
        status: params.status,
      },
    });
  },

  async createLegalHold(data) {
    return apiClient("/data-governance/legal-holds", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  async releaseLegalHold(id, data) {
    return apiClient(`/data-governance/legal-holds/${id}/release`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Compliance Evidence.
   */
  async listEvidence(params = {}) {
    return apiClient("/data-governance/evidence", {
      params: {
        workspace_id: params.workspaceId,
        evidence_type: params.evidenceType,
        subject_id: params.subjectId,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  async getEvidence(id) {
    return apiClient(`/data-governance/evidence/${id}`);
  },

  /**
   * Reports.
   */
  async getRetentionReport() {
    return apiClient("/data-governance/reports/retention");
  },

  async getClassificationReport() {
    return apiClient("/data-governance/reports/classification");
  },

  async getAccessReport() {
    return apiClient("/data-governance/reports/access");
  },

  async getDeletionReport() {
    return apiClient("/data-governance/reports/deletion");
  },

  async getEvidenceReport() {
    return apiClient("/data-governance/reports/evidence");
  },
};

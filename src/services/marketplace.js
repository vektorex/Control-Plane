import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 38: AI Workflow Marketplace, Versioned Templates & Extension Ecosystem.
 *
 * NOTE: Marketplace packages are reusable platform definitions and configurations.
 * Installation does not automatically grant permissions, credentials, or unrestricted access.
 */
export const marketplaceService = {
  /**
   * List marketplace packages with search and filtering.
   */
  async listPackages(params = {}) {
    const q = new URLSearchParams();
    if (params.query) q.set("query", params.query);
    if (params.category) q.set("category", params.category);
    if (params.packageType) q.set("package_type", params.packageType);
    if (params.visibility) q.set("visibility", params.visibility);
    if (params.status) q.set("status", params.status);
    if (params.limit) q.set("limit", params.limit);
    if (params.offset) q.set("offset", params.offset);
    const qs = q.toString();
    return apiClient(`/marketplace/packages${qs ? `?${qs}` : ""}`);
  },

  /**
   * Create a new package (draft).
   */
  async createPackage(data) {
    return apiClient("/marketplace/packages", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get package by slug.
   */
  async getPackageBySlug(slug) {
    return apiClient(`/marketplace/packages/slug/${encodeURIComponent(slug)}`);
  },

  /**
   * Get package by ID.
   */
  async getPackage(packageId) {
    return apiClient(`/marketplace/packages/id/${packageId}`);
  },

  /**
   * Update package metadata.
   */
  async updatePackage(packageId, data) {
    return apiClient(`/marketplace/packages/id/${packageId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List versions of a package.
   */
  async listVersions(packageId) {
    return apiClient(`/marketplace/packages/${packageId}/versions`);
  },

  /**
   * Create a new version for a package.
   */
  async createVersion(packageId, data) {
    return apiClient(`/marketplace/packages/${packageId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get version detail.
   */
  async getVersion(packageId, versionId) {
    return apiClient(`/marketplace/packages/${packageId}/versions/${versionId}`);
  },

  /**
   * Publish a package version through the 7-stage publishing pipeline.
   */
  async publishVersion(packageId, versionId) {
    return apiClient(`/marketplace/packages/${packageId}/versions/${versionId}/publish`, {
      method: "POST",
    });
  },

  /**
   * Deprecate a package version.
   */
  async deprecateVersion(packageId, versionId) {
    return apiClient(`/marketplace/packages/${packageId}/versions/${versionId}/deprecate`, {
      method: "POST",
    });
  },

  /**
   * Revoke a package version.
   */
  async revokeVersion(packageId, versionId, reason = "") {
    return apiClient(`/marketplace/packages/${packageId}/versions/${versionId}/revoke`, {
      method: "POST",
      body: JSON.stringify({ reason }),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Install a package into a workspace.
   */
  async installPackage(packageId, data) {
    return apiClient(`/marketplace/packages/${packageId}/install`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List installations.
   */
  async listInstallations(params = {}) {
    const q = new URLSearchParams();
    if (params.workspaceId) q.set("workspace_id", params.workspaceId);
    if (params.status) q.set("status", params.status);
    const qs = q.toString();
    return apiClient(`/marketplace/installations${qs ? `?${qs}` : ""}`);
  },

  /**
   * Get installation detail.
   */
  async getInstallation(installationId) {
    return apiClient(`/marketplace/installations/${installationId}`);
  },

  /**
   * Update an installed package to a new version.
   */
  async updateInstallation(installationId, data = {}) {
    return apiClient(`/marketplace/installations/${installationId}/update`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Roll back an installed package to its previous or target version.
   */
  async rollbackInstallation(installationId, data = {}) {
    return apiClient(`/marketplace/installations/${installationId}/rollback`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Uninstall a package.
   */
  async uninstall(installationId) {
    return apiClient(`/marketplace/installations/${installationId}`, {
      method: "DELETE",
    });
  },

  /**
   * Fork a package into the caller's organization.
   */
  async forkPackage(packageId, data) {
    return apiClient(`/marketplace/packages/${packageId}/fork`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get package usage analytics.
   */
  async getUsage(packageId) {
    return apiClient(`/marketplace/packages/${packageId}/usage`);
  },

  /**
   * List categories.
   */
  async getCategories() {
    return apiClient("/marketplace/categories");
  },

  /**
   * List taxonomy tags.
   */
  async getTags() {
    return apiClient("/marketplace/tags");
  },

  /**
   * List user reviews for a package.
   */
  async listReviews(packageId) {
    return apiClient(`/marketplace/packages/${packageId}/reviews`);
  },

  /**
   * Submit a user review.
   */
  async submitReview(packageId, data) {
    return apiClient(`/marketplace/packages/${packageId}/reviews`, {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Preview and pre-validate package manifest (permissions, dependencies, security).
   */
  async previewManifest(manifest) {
    return apiClient("/marketplace/preview", {
      method: "POST",
      body: JSON.stringify(manifest),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Execute package sandbox dry-run with mock inputs.
   */
  async runSandbox(data) {
    return apiClient("/marketplace/sandbox/test", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },
};

import { apiClient } from "@/lib/api";

/**
 * Frontend client service for Step 36: Disaster Recovery, Backup & Business Continuity Layer.
 */
export const recoveryService = {
  /**
   * Fetch disaster recovery overview statistics.
   */
  async getOverview() {
    return apiClient("/recovery/overview");
  },

  /**
   * List backup policies.
   */
  async listPolicies(params = {}) {
    return apiClient("/recovery/policies", {
      params: {
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Create backup policy.
   */
  async createPolicy(data) {
    return apiClient("/recovery/policies", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Delete backup policy.
   */
  async deletePolicy(policyId) {
    return apiClient(`/recovery/policies/${policyId}`, {
      method: "DELETE",
    });
  },

  /**
   * List backups.
   */
  async listBackups(params = {}) {
    return apiClient("/recovery/backups", {
      params: {
        status: params.status,
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Orchestrate and execute a logical backup.
   */
  async createBackup(data = {}) {
    return apiClient("/recovery/backups", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get single backup with manifest and verifications.
   */
  async getBackup(backupId) {
    return apiClient(`/recovery/backups/${backupId}`);
  },

  /**
   * Verify backup integrity and simulation.
   */
  async verifyBackup(backupId) {
    return apiClient(`/recovery/backups/${backupId}/verify`, {
      method: "POST",
    });
  },

  /**
   * Mark backup expired.
   */
  async expireBackup(backupId) {
    return apiClient(`/recovery/backups/${backupId}/expire`, {
      method: "POST",
    });
  },

  /**
   * Get backup manifest.
   */
  async getManifest(manifestId) {
    return apiClient(`/recovery/manifests/${manifestId}`);
  },

  /**
   * Create restore plan.
   */
  async createRestorePlan(data) {
    return apiClient("/recovery/restore-plans", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List restore plans.
   */
  async listRestorePlans(params = {}) {
    return apiClient("/recovery/restore-plans", {
      params: {
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Get single restore plan.
   */
  async getRestorePlan(planId) {
    return apiClient(`/recovery/restore-plans/${planId}`);
  },

  /**
   * Run dry-run restore simulation.
   */
  async dryRunRestorePlan(planId) {
    return apiClient(`/recovery/restore-plans/${planId}/dry-run`, {
      method: "POST",
    });
  },

  /**
   * Approve restore plan.
   */
  async approveRestorePlan(planId) {
    return apiClient(`/recovery/restore-plans/${planId}/approve`, {
      method: "POST",
    });
  },

  /**
   * Execute approved restore plan.
   */
  async executeRestorePlan(planId) {
    return apiClient(`/recovery/restore-plans/${planId}/execute`, {
      method: "POST",
    });
  },

  /**
   * List restore execution runs.
   */
  async listRestores(params = {}) {
    return apiClient("/recovery/restores", {
      params: {
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Get single restore run details.
   */
  async getRestore(restoreId) {
    return apiClient(`/recovery/restores/${restoreId}`);
  },

  /**
   * List recovery objectives (RTO/RPO).
   */
  async listObjectives() {
    return apiClient("/recovery/objectives");
  },

  /**
   * Create recovery objective.
   */
  async createObjective(data) {
    return apiClient("/recovery/objectives", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get recovery readiness assessment.
   */
  async getReadiness() {
    return apiClient("/recovery/readiness");
  },

  /**
   * List business continuity plans.
   */
  async listContinuityPlans() {
    return apiClient("/recovery/continuity-plans");
  },

  /**
   * Create business continuity plan.
   */
  async createContinuityPlan(data) {
    return apiClient("/recovery/continuity-plans", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * List recovery exercises.
   */
  async listExercises(params = {}) {
    return apiClient("/recovery/exercises", {
      params: {
        limit: params.limit || 50,
        offset: params.offset || 0,
      },
    });
  },

  /**
   * Create recovery exercise.
   */
  async createExercise(data) {
    return apiClient("/recovery/exercises", {
      method: "POST",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  },

  /**
   * Get recovery exercise details with observations.
   */
  async getExercise(exerciseId) {
    return apiClient(`/recovery/exercises/${exerciseId}`);
  },

  /**
   * Execute recovery exercise.
   */
  async runExercise(exerciseId) {
    return apiClient(`/recovery/exercises/${exerciseId}/run`, {
      method: "POST",
    });
  },

  /**
   * Abort in-flight recovery exercise.
   */
  async abortExercise(exerciseId, reason) {
    return apiClient(`/recovery/exercises/${exerciseId}/abort`, {
      method: "POST",
      params: { reason },
    });
  },
};

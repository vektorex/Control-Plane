import { apiClient } from "@/lib/api";

/**
 * Service for the AI Execution Replay & Debugging Studio (Step 21).
 * Provides safe historical execution inspection, dry-run simulation,
 * side-effect isolation, factual diff comparison, and error analysis.
 */
export const replayService = {
  /**
   * Inspect historical execution snapshot in read-only mode without re-execution.
   */
  async inspectRunReplay(runId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/runs/${runId}/replay/inspect`, {
      method: "POST",
      headers,
    });
  },

  /**
   * Run simulation in safe dry-run mode (external side-effects simulated).
   */
  async dryRunReplay(runId, overrides = null, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/runs/${runId}/replay/dry-run`, {
      method: "POST",
      headers,
      body: {
        mode: "dry_run",
        dry_run: true,
        overrides: overrides || undefined,
      },
    });
  },

  /**
   * Re-execute eligible AI computation. Side effects remain dry-run by default.
   */
  async executeReplay(runId, { overrides = null, dryRun = true } = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/runs/${runId}/replay`, {
      method: "POST",
      headers,
      body: {
        mode: "replay",
        dry_run: dryRun,
        overrides: overrides || undefined,
      },
    });
  },

  /**
   * Pre-flight check to verify whether run components (task, model, tools) are available.
   */
  async checkEligibility(runId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/runs/${runId}/replay/eligibility`, {
      method: "GET",
      headers,
    });
  },

  /**
   * Replay an individual execution step safely in isolation.
   */
  async replayStep(runId, stepId, { dryRun = true, overrides = null } = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/runs/${runId}/steps/${stepId}/replay`, {
      method: "POST",
      headers,
      body: {
        dry_run: dryRun,
        overrides: overrides || undefined,
      },
    });
  },

  /**
   * Retrieve normalized failure insights and diagnostics for a failed run.
   */
  async getFailureInsights(runId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/runs/${runId}/failure-insights`, {
      method: "GET",
      headers,
    });
  },

  /**
   * List replays with pagination and filtering.
   */
  async listReplays(params = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient("/replays", {
      method: "GET",
      headers,
      params,
    });
  },

  /**
   * Retrieve details and snapshot of a single ReplayRun.
   */
  async getReplay(replayId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/replays/${replayId}`, {
      method: "GET",
      headers,
    });
  },

  /**
   * Retrieve ordered timeline trace events for replay debugging.
   */
  async getReplayTrace(replayId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/replays/${replayId}/trace`, {
      method: "GET",
      headers,
    });
  },

  /**
   * Cooperatively cancel an in-flight replay run.
   */
  async cancelReplay(replayId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/replays/${replayId}/cancel`, {
      method: "POST",
      headers,
    });
  },

  /**
   * Retrieve factual diff comparison between original and replay executions.
   */
  async compareReplay(replayId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/replays/${replayId}/compare`, {
      method: "GET",
      headers,
    });
  },

  /**
   * Workflow Replay: inspect historical workflow run.
   */
  async inspectWorkflowReplay(workflowRunId, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/workflow-runs/${workflowRunId}/replay/inspect`, {
      method: "POST",
      headers,
    });
  },

  /**
   * Workflow Replay: dry-run simulation of workflow run.
   */
  async dryRunWorkflowReplay(workflowRunId, overrides = null, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/workflow-runs/${workflowRunId}/replay/dry-run`, {
      method: "POST",
      headers,
      body: {
        mode: "dry_run",
        dry_run: true,
        overrides: overrides || undefined,
      },
    });
  },

  /**
   * Workflow Replay: re-execute workflow.
   */
  async executeWorkflowReplay(workflowRunId, { overrides = null, dryRun = true } = {}, workspaceId) {
    const headers = workspaceId ? { "X-Workspace-Id": workspaceId } : {};
    return apiClient(`/workflow-runs/${workflowRunId}/replay`, {
      method: "POST",
      headers,
      body: {
        mode: "replay",
        dry_run: dryRun,
        overrides: overrides || undefined,
      },
    });
  },
};

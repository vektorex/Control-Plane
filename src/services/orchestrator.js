import { apiClient } from "@/lib/api";
import { env } from "@/config/env";

/**
 * Service contracts for the Python/FastAPI Orchestration Layer.
 */
export const orchestratorService = {
  /**
   * Health check to verify FastAPI orchestration backend status
   */
  async getHealth() {
    return apiClient("/health");
  },

  /**
   * Fetch available models and provider status from the backend abstraction layer
   */
  async getModels() {
    return apiClient("/models");
  },

  /**
   * Execute standard completion via LLM abstraction layer
   */
  async generate(payload) {
    return apiClient("/llm/generate", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Execute streaming completion via Server-Sent Events (SSE)
   */
  async generateStream(payload, { onChunk, onError, onComplete, signal }) {
    const url = `${env.orchestrator.apiUrl}/llm/generate/stream`;
    try {
      let authHeader = env.orchestrator.apiSecret ? `Bearer ${env.orchestrator.apiSecret}` : "";
      try {
        const { supabase } = await import("@/lib/supabaseClient");
        const { data } = await supabase.auth.getSession();
        if (data?.session?.access_token) {
          authHeader = `Bearer ${data.session.access_token}`;
        }
      } catch {}

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
        body: JSON.stringify(payload),
        signal,
      });


      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData?.error?.message ||
            errorData?.detail ||
            `Streaming request failed with HTTP ${response.status}`
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const dataStr = trimmed.slice(5).trim();
          if (dataStr === "[DONE]") {
            onComplete?.();
            return;
          }

          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.error) {
              onError?.(new Error(parsed.error.message || "Streaming error from provider"));
              return;
            }
            onChunk?.(parsed);
          } catch (err) {
            console.error("[StreamParser] Error parsing chunk:", err, dataStr);
          }
        }
      }

      onComplete?.();
    } catch (err) {
      if (err.name === "AbortError") {
        console.log("[Stream] Aborted by user");
        return;
      }
      onError?.(err);
    }
  },

  /**
   * Fetch system engine stats and active execution metrics
   */
  async getMetrics() {
    return apiClient("/metrics");
  },

  /**
   * List orchestrated work tasks with optional filtering
   */
  async getTasks(params = {}) {
    return apiClient("/tasks", { params });
  },

  /**
   * Retrieve a single task's execution graph and status
   */
  async getTask(taskId) {
    return apiClient(`/tasks/${taskId}`);
  },

  /**
   * Create and submit a task to the orchestration queue
   */
  async createTask(payload) {
    return apiClient("/tasks", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * List registered projects/workspaces
   */
  async getProjects() {
    return apiClient("/projects");
  },

  /**
   * Create a new project workspace
   */
  async createProject(payload) {
    return apiClient("/projects", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Retrieve orchestrator engine settings & provider statuses
   */
  async getOrchestratorConfig() {
    return apiClient("/settings/orchestration");
  },

  /**
   * Update orchestrator engine settings
   */
  async updateOrchestratorConfig(payload) {
    return apiClient("/settings/orchestration", {
      method: "PUT",
      body: payload,
    });
  },
};

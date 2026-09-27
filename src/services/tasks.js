import { apiClient } from "@/lib/api";
import { env } from "@/config/env";

export const taskService = {
  /**
   * List all tasks across the platform
   */
  async listTasks(params = {}) {
    return apiClient("/tasks", { params });
  },

  /**
   * Get single task by ID
   */
  async getTask(taskId) {
    return apiClient(`/tasks/${taskId}`);
  },

  /**
   * Create a new task under a project
   */
  async createTask(projectId, payload) {
    return apiClient(`/projects/${projectId}/tasks`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Update task details (title, description, instructions, context_text, status)
   */
  async updateTask(taskId, payload) {
    return apiClient(`/tasks/${taskId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Delete a task
   */
  async deleteTask(taskId) {
    return apiClient(`/tasks/${taskId}`, {
      method: "DELETE",
    });
  },

  /**
   * List runs belonging to a task
   */
  async listTaskRuns(taskId, params = {}) {
    return apiClient(`/tasks/${taskId}/runs`, { params });
  },

  /**
   * Execute task synchronously and return persisted Run
   */
  async executeTask(taskId, payload) {
    return apiClient(`/tasks/${taskId}/run`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Execute task via Server-Sent Events (SSE) streaming
   */
  async executeTaskStream(taskId, payload, { onChunk, onRunStart, onRunCompleted, onError, onComplete, signal }) {
    const url = `${env.orchestrator.apiUrl}/tasks/${taskId}/run/stream`;
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
            `Task execution failed with HTTP ${response.status}`
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
            if (parsed.type === "run_start") {
              onRunStart?.(parsed);
            } else if (parsed.type === "content_delta") {
              onChunk?.(parsed.delta);
            } else if (parsed.type === "run_completed") {
              onRunCompleted?.(parsed.run);
            } else if (parsed.type === "error" || parsed.error) {
              onError?.(new Error(parsed.error?.message || parsed.error || "Streaming error during task execution"));
              return;
            }
          } catch (err) {
            console.error("[TaskStreamParser] Error parsing chunk:", err, dataStr);
          }
        }
      }

      onComplete?.();
    } catch (err) {
      if (err.name === "AbortError") {
        console.log("[TaskStream] Aborted by user");
        return;
      }
      onError?.(err);
    }
  },
};

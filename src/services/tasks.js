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
  async executeTaskStream(
    taskId,
    payload,
    {
      onChunk,
      onRunStart,
      onRunCompleted,
      onError,
      onComplete,
      onPlanningStart,
      onPlanGenerated,
      onStepStart,
      onStepCompleted,
      onStepFailed,
      onEvaluating,
      onEvaluationCompleted,
      onEvaluationStart,
      onEvaluationCheck,
      onRevisionStart,
      onRevisionCompleted,
      onModelSelected,
      onModelFallback,
      onReplanGenerated,
      signal,
    }
  ) {
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
            } else if (parsed.type === "model_selected") {
              onModelSelected?.(parsed);
            } else if (parsed.type === "model_fallback") {
              onModelFallback?.(parsed);
            } else if (parsed.type === "planning_start") {
              onPlanningStart?.(parsed);
            } else if (parsed.type === "plan_generated") {
              onPlanGenerated?.(parsed.plan);
            } else if (parsed.type === "step_start") {
              onStepStart?.(parsed.step);
            } else if (parsed.type === "step_completed") {
              onStepCompleted?.(parsed.step);
            } else if (parsed.type === "step_failed") {
              onStepFailed?.(parsed.step);
            } else if (parsed.type === "evaluating") {
              onEvaluating?.(parsed);
            } else if (parsed.type === "evaluation_start") {
              onEvaluationStart?.(parsed);
            } else if (parsed.type === "evaluation_check") {
              onEvaluationCheck?.(parsed.check);
            } else if (parsed.type === "evaluation_completed") {
              onEvaluationCompleted?.(parsed.result || parsed.evaluation);
            } else if (parsed.type === "revision_start") {
              onRevisionStart?.(parsed);
            } else if (parsed.type === "revision_completed") {
              onRevisionCompleted?.(parsed);
            } else if (parsed.type === "replan_generated") {
              onReplanGenerated?.(parsed.plan, parsed.iteration);
            } else if (parsed.type === "chunk" || parsed.type === "content_delta") {
              onChunk?.(parsed.content ?? parsed.delta ?? "");
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

  /**
   * Preview deterministic ExecutionPlan for a task without executing it (Step 10 Orchestrator)
   */
  async planTask(taskId, payload = {}) {
    return apiClient(`/tasks/${taskId}/plan`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Preview model routing and requirement extraction for a task (Step 12 Model Intelligence)
   */
  async previewTaskModel(taskId, payload = {}) {
    return apiClient(`/tasks/${taskId}/model-preview`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Preview intelligent retrieval routing decision for a task (Step 8 dev debug)
   */
  async previewTaskRetrieval(taskId, payload = {}) {
    return apiClient(`/tasks/${taskId}/retrieval/preview`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * List context items associated with a task
   */
  async listTaskContexts(taskId, params = {}) {
    return apiClient(`/tasks/${taskId}/context`, { params });
  },

  /**
   * Create a manual context item for a task
   */
  async createTaskContext(taskId, payload) {
    return apiClient(`/tasks/${taskId}/context`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Inspect assembled context package from ContextEngine (debug/dev view)
   */
  async inspectTaskContext(taskId, maxContextTokens = 8000) {
    return apiClient(`/tasks/${taskId}/context/inspect`, {
      params: { max_context_tokens: maxContextTokens },
    });
  },

  /**
   * Update an individual context item
   */
  async updateContext(contextId, payload) {
    return apiClient(`/context/${contextId}`, {
      method: "PATCH",
      body: payload,
    });
  },

  /**
   * Delete a context item
   */
  async deleteContext(contextId) {
    return apiClient(`/context/${contextId}`, {
      method: "DELETE",
    });
  },

  /**
   * Evaluate task execution output (Step 13 Evaluation & Verification)
   */
  async evaluateTask(taskId, payload = {}) {
    return apiClient(`/tasks/${taskId}/evaluate`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Get evaluation history and verification findings for a run (Step 13)
   */
  /**
   * Analyze task to determine execution requirements (Step 20 Task Intelligence)
   */
  async analyzeTask(payload = {}) {
    return apiClient("/tasks/analyze", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Analyze an existing task by taskId (Step 20)
   */
  async analyzeExistingTask(taskId, payload = {}) {
    return apiClient(`/tasks/${taskId}/analyze`, {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Preview execution requirements without executing (Step 20)
   */
  async previewExecution(payload = {}) {
    return apiClient("/tasks/preview-execution", {
      method: "POST",
      body: payload,
    });
  },

  /**
   * Preview execution for an existing task by taskId (Step 20)
   */
  async previewExistingTaskExecution(taskId, payload = {}) {
    return apiClient(`/tasks/${taskId}/preview-execution`, {
      method: "POST",
      body: payload,
    });
  },
};


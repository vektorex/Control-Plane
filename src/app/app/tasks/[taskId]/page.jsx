"use client";

import React, { useState, useEffect, useRef, use } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { taskService } from "@/services/tasks";
import { orchestratorService } from "@/services/orchestrator";
import { toolService } from "@/services/tools";
import { formatDate } from "@/lib/utils";
import {
  Play,
  Square,
  Sparkles,
  Zap,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  Clock,
  ArrowLeft,
  Save,
  FileText,
  History,
  Terminal,
  Calendar,
  Plus,
  Trash2,
  Edit3,
  Layers,
  Sliders,
  Database,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Code,
  Compass,
  ChevronDown,
  ChevronUp,
  GitBranch,
  Network,
  Search,
  HelpCircle,
  Cpu,
  SlidersHorizontal,
  Globe,
  ExternalLink,
  Wrench,
  ShieldCheck,
  ListOrdered,
  Loader2,
  XCircle,
  Workflow,
  Coins,
  Shield,
  Activity,
  CheckSquare,
} from "lucide-react";

export default function TaskWorkspacePage({ params: paramsProp }) {
  const router = useRouter();
  const routeParams = useParams();
  const taskId = routeParams?.taskId || (paramsProp ? use(paramsProp)?.taskId : null);

  // Task state
  const [task, setTask] = useState(null);
  const [title, setTitle] = useState("");
  const [instructions, setInstructions] = useState("");
  const [contextText, setContextText] = useState("");
  const [taskStatus, setTaskStatus] = useState("draft");
  const [isSavingTask, setIsSavingTask] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Manual Context state (Step 6)
  const [contexts, setContexts] = useState([]);
  const [isLoadingContexts, setIsLoadingContexts] = useState(false);
  const [isContextModalOpen, setIsContextModalOpen] = useState(false);
  const [editingContext, setEditingContext] = useState(null);
  const [modalTitle, setModalTitle] = useState("");
  const [modalContent, setModalContent] = useState("");
  const [modalPriority, setModalPriority] = useState(50);
  const [isSavingContext, setIsSavingContext] = useState(false);
  const [contextError, setContextError] = useState(null);

  // Context Inspector / Debug view state (Step 6)
  const [showInspector, setShowInspector] = useState(false);
  const [inspectData, setInspectData] = useState(null);
  const [isLoadingInspect, setIsLoadingInspect] = useState(false);
  const [contextBudget, setContextBudget] = useState(8000);

  // Models & execution settings
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [temperature, setTemperature] = useState(0.2);
  const [enableStreaming, setEnableStreaming] = useState(true);

  // Step 8: Intelligent Retrieval Router settings
  const [retrievalMode, setRetrievalMode] = useState("auto"); // "auto" | "always" | "never"
  const [retrievalStrategy, setRetrievalStrategy] = useState(""); // "" (auto), "hybrid", "vector", "keyword", "multi_query"
  const [retrievalScope, setRetrievalScope] = useState("project"); // "project" | "workspace"
  const [retrievalTopK, setRetrievalTopK] = useState(8);
  const [showAdvancedRetrieval, setShowAdvancedRetrieval] = useState(false);

  // Step 9: Tools & Web Search settings
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const [webSearchQuery, setWebSearchQuery] = useState("");
  const [webSearchLimit, setWebSearchLimit] = useState(5);
  const [webSearchRecencyDays, setWebSearchRecencyDays] = useState("");
  // Step 10 & 11: Execution Plan & LLM Planning state
  const [plannerMode, setPlannerMode] = useState("hybrid"); // "hybrid" (Auto) | "deterministic" | "llm"
  const [planningState, setPlanningState] = useState(null); // null | "analyzing" | "evaluating" | "replanning"
  const [completionEvaluation, setCompletionEvaluation] = useState(null);
  const [iterationCount, setIterationCount] = useState(1);
  const [repairCount, setRepairCount] = useState(0);
  const [executionPlan, setExecutionPlan] = useState(null);
  const [isLoadingPlan, setIsLoadingPlan] = useState(false);
  const [planError, setPlanError] = useState(null);
  const [liveSteps, setLiveSteps] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(null);

  // Retrieval Router Preview / Debug state (Step 8)
  const [previewDecision, setPreviewDecision] = useState(null);
  const [isPreviewingRetrieval, setIsPreviewingRetrieval] = useState(false);
  const [previewError, setPreviewError] = useState(null);


  // Step 12: Model Intelligence & Model Router settings
  const [modelMode, setModelMode] = useState("auto"); // "auto" | "manual"
  const [latencyPreference, setLatencyPreference] = useState("balanced"); // "low" | "balanced" | "high_quality"
  const [costPreference, setCostPreference] = useState("balanced"); // "low" | "balanced" | "quality"
  const [modelPreview, setModelPreview] = useState(null);
  const [isPreviewingModel, setIsPreviewingModel] = useState(false);
  const [modelPreviewError, setModelPreviewError] = useState(null);
  const [fallbackEvent, setFallbackEvent] = useState(null);

  // Step 13: Evaluation & Verification Engine state
  const [evaluationMode, setEvaluationMode] = useState("standard"); // "standard" | "strict" | "basic" | "off"
  const [strictEvaluation, setStrictEvaluation] = useState(false);
  const [expectedFormat, setExpectedFormat] = useState(""); // "" | "json" | "markdown" | "bullet_list" | "table" | "code"
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isRevising, setIsRevising] = useState(false);
  const [revisionAttempts, setRevisionAttempts] = useState(0);
  const [evaluationError, setEvaluationError] = useState(null);

  // Execution & Run state
  const [activeRun, setActiveRun] = useState(null);
  const [runs, setRuns] = useState([]);
  const [isLoadingTask, setIsLoadingTask] = useState(true);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [outputStream, setOutputStream] = useState("");
  const [executionError, setExecutionError] = useState(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [copied, setCopied] = useState(false);

  // Refs for aborting and latency timing
  const abortControllerRef = useRef(null);
  const timerRef = useRef(null);

  // Load models from GET /api/models
  const loadModels = async () => {
    try {
      const data = await orchestratorService.getModels();
      if (data?.models?.length > 0) {
        setModels(data.models);
        if (!selectedModel) {
          const defaultModel = data.models.find((m) => m.is_default) || data.models[0];
          setSelectedModel(defaultModel.id);
        }
      }
    } catch (err) {
      console.error("[TaskWorkspace] Failed to fetch models:", err);
    }
  };

  // Load task and context
  const loadTaskAndContexts = async () => {
    if (!taskId) return;
    try {
      setIsLoadingTask(true);
      setExecutionError(null);

      const taskData = await taskService.getTask(taskId);
      setTask(taskData);
      setTitle(taskData.title || "");
      setInstructions(taskData.instructions || taskData.description || "");
      setContextText(taskData.context_text || "");
      setTaskStatus(taskData.status || "draft");
      if (taskData.model_mode) {
        setModelMode(taskData.model_mode);
      }
      if (taskData.preferred_model) {
        setSelectedModel(taskData.preferred_model);
      }
      if (taskData.evaluation_mode) {
        setEvaluationMode(taskData.evaluation_mode);
      }
      if (taskData.strict_evaluation !== undefined) {
        setStrictEvaluation(taskData.strict_evaluation);
      }
      if (taskData.expected_format) {
        setExpectedFormat(taskData.expected_format);
      }

      // Fetch contexts and runs in parallel
      await Promise.all([fetchTaskContexts(), fetchTaskRuns()]);
    } catch (err) {
      console.error("[TaskWorkspace] Error loading task:", err);
      setExecutionError(err.message || "Failed to load task details");
    } finally {
      setIsLoadingTask(false);
    }
  };

  const fetchTaskContexts = async () => {
    if (!taskId) return;
    try {
      setIsLoadingContexts(true);
      const data = await taskService.listTaskContexts(taskId);
      setContexts(data?.contexts || []);
    } catch (err) {
      console.error("[TaskWorkspace] Error loading contexts:", err);
    } finally {
      setIsLoadingContexts(false);
    }
  };

  const fetchTaskRuns = async () => {
    if (!taskId) return;
    try {
      setIsLoadingRuns(true);
      const runsData = await taskService.listTaskRuns(taskId);
      const runsList = runsData?.runs || [];
      setRuns(runsList);
      if (runsList.length > 0 && !activeRun) {
        setActiveRun(runsList[0]);
        setOutputStream(runsList[0].output_content || "");
        if (runsList[0].evaluation_result) {
          setEvaluationResult(runsList[0].evaluation_result);
        }
        if (runsList[0].revision_attempts !== undefined) {
          setRevisionAttempts(runsList[0].revision_attempts);
        }
      }
    } catch (err) {
      console.error("[TaskWorkspace] Error loading runs:", err);
    } finally {
      setIsLoadingRuns(false);
    }
  };

  // Inspect context assembly from ContextEngine
  const handleInspectContext = async () => {
    if (!taskId) return;
    try {
      setIsLoadingInspect(true);
      setShowInspector(true);
      const data = await taskService.inspectTaskContext(taskId, contextBudget);
      setInspectData(data);
    } catch (err) {
      console.error("[TaskWorkspace] Error inspecting context:", err);
    } finally {
      setIsLoadingInspect(false);
    }
  };

  // Step 8: Preview Retrieval Router Decision
  const handlePreviewRetrieval = async () => {
    if (!taskId) return;
    try {
      setIsPreviewingRetrieval(true);
      setPreviewError(null);
      // Auto-save any updated instructions first
      try {
        await taskService.updateTask(taskId, {
          title: title.trim(),
          instructions: instructions.trim(),
          context_text: contextText.trim() || null,
        });
      } catch {}

      const payload = {
        retrieval_mode: retrievalMode,
        retrieval_strategy: retrievalStrategy || undefined,
        retrieval_scope: retrievalScope,
        retrieval_top_k: Number(retrievalTopK),
      };

      const res = await taskService.previewTaskRetrieval(taskId, payload);
      setPreviewDecision(res.decision);
    } catch (err) {
      console.error("[TaskWorkspace] Error previewing retrieval:", err);
      setPreviewError(err.message || "Failed to preview retrieval decision.");
    } finally {
      setIsPreviewingRetrieval(false);
    }
  };

  // Step 10: Preview Deterministic Execution Plan
  const handlePreviewPlan = async () => {
    if (!taskId) return;
    try {
      setIsLoadingPlan(true);
      setPlanError(null);
      // Auto-save updated instructions first
      try {
        await taskService.updateTask(taskId, {
          title: title.trim(),
          instructions: instructions.trim(),
          context_text: contextText.trim() || null,
        });
      } catch {}

      const payload = {
        model: selectedModel || undefined,
        planner_mode: plannerMode,
        temperature: Number(temperature),
        max_context_tokens: Number(contextBudget),
        retrieval_mode: retrievalMode,
        retrieval_strategy: retrievalStrategy || undefined,
        retrieval_scope: retrievalScope,
        retrieval_top_k: Number(retrievalTopK),
        retrieval_project_scope: retrievalScope === "project",
        enable_web_search: enableWebSearch,
        web_search_query: webSearchQuery.trim() || undefined,
        web_search_limit: Number(webSearchLimit) || 5,
        web_search_recency_days: webSearchRecencyDays ? Number(webSearchRecencyDays) : undefined,
        tool_mode: enableWebSearch ? "enabled" : "disabled",
        tools_enabled: enableWebSearch ? ["web_search"] : [],
      };

      const plan = await taskService.planTask(taskId, payload);
      setExecutionPlan(plan);
      if (plan?.metadata?.repair_count !== undefined) {
        setRepairCount(plan.metadata.repair_count);
      }
      if (plan?.steps) {
        setLiveSteps(
          plan.steps.map((st, idx) => ({
            id: st.id,
            step_index: idx + 1,
            step_type: st.type,
            status: "pending",
            tool_name: st.tool,
            retrieval_strategy: st.strategy,
            model: st.model,
          }))
        );
      }
    } catch (err) {
      console.error("[TaskWorkspace] Error previewing plan:", err);
      setPlanError(err.message || "Failed to generate execution plan");
    } finally {
      setIsLoadingPlan(false);
    }
  };

  // Step 12: Preview Model Selection & Requirements
  const handlePreviewModel = async () => {
    if (!taskId) return;
    try {
      setIsPreviewingModel(true);
      setModelPreviewError(null);
      // Auto-save updated instructions first
      try {
        await taskService.updateTask(taskId, {
          title: title.trim(),
          instructions: instructions.trim(),
          context_text: contextText.trim() || null,
        });
      } catch {}

      const payload = {
        model_mode: modelMode,
        model: modelMode === "manual" ? selectedModel : undefined,
        latency_preference: latencyPreference,
        cost_preference: costPreference,
        enable_web_search: enableWebSearch,
        tools_enabled: enableWebSearch ? ["web_search"] : [],
      };

      const res = await taskService.previewTaskModel(taskId, payload);
      setModelPreview(res);
    } catch (err) {
      console.error("[TaskWorkspace] Error previewing model selection:", err);
      setModelPreviewError(err.message || "Failed to preview model selection.");
    } finally {
      setIsPreviewingModel(false);
    }
  };

  const loadAvailableTools = async () => {
    try {
      const res = await toolService.listTools();
      setAvailableTools(res?.tools || []);
    } catch (err) {
      console.warn("[TaskWorkspace] Error loading tools:", err);
    }
  };

  useEffect(() => {
    loadModels();
    loadTaskAndContexts();
    loadAvailableTools();
  }, [taskId]);

  // Save task modifications (title, instructions, context_text)
  const handleSaveTask = async () => {
    if (!taskId) return;
    try {
      setIsSavingTask(true);
      setSaveSuccess(false);
      setExecutionError(null);

      const updated = await taskService.updateTask(taskId, {
        title: title.trim(),
        instructions: instructions.trim(),
        context_text: contextText.trim() || null,
        status: taskStatus,
        model_mode: modelMode,
        preferred_model: modelMode === "manual" ? selectedModel : null,
        evaluation_mode: evaluationMode,
        strict_evaluation: strictEvaluation,
        expected_format: expectedFormat || null,
      });

      setTask(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      setExecutionError(`Failed to save task: ${err.message}`);
    } finally {
      setIsSavingTask(false);
    }
  };

  // Step 13: Manual Output Verification Trigger
  const handleManualEvaluate = async () => {
    if (!taskId) return;
    try {
      setIsEvaluating(true);
      setEvaluationError(null);
      const res = await taskService.evaluateTask(taskId, {
        mode: evaluationMode,
        strict: strictEvaluation,
        expected_format: expectedFormat || undefined,
      });
      if (res?.result) {
        setEvaluationResult(res.result);
      }
      await fetchTaskRuns();
    } catch (err) {
      console.error("[TaskWorkspace] Evaluation failed:", err);
      setEvaluationError(err.message || "Failed to evaluate task output");
    } finally {
      setIsEvaluating(false);
    }
  };

  // Manual Context Modal Handlers
  const handleOpenAddContextModal = () => {
    setEditingContext(null);
    setModalTitle("");
    setModalContent("");
    setModalPriority(50);
    setContextError(null);
    setIsContextModalOpen(true);
  };

  const handleOpenEditContextModal = (ctx) => {
    setEditingContext(ctx);
    setModalTitle(ctx.title || "");
    setModalContent(ctx.content || "");
    setModalPriority(ctx.priority || 50);
    setContextError(null);
    setIsContextModalOpen(true);
  };

  const handleSaveContextItem = async (e) => {
    e?.preventDefault();
    if (!taskId || !modalTitle.trim() || !modalContent.trim()) return;

    try {
      setIsSavingContext(true);
      setContextError(null);

      if (editingContext) {
        await taskService.updateContext(editingContext.id, {
          title: modalTitle.trim(),
          content: modalContent.trim(),
          priority: Number(modalPriority),
        });
      } else {
        await taskService.createTaskContext(taskId, {
          title: modalTitle.trim(),
          content: modalContent.trim(),
          priority: Number(modalPriority),
          source_type: "manual",
        });
      }

      setIsContextModalOpen(false);
      await fetchTaskContexts();
      if (showInspector) {
        await handleInspectContext();
      }
    } catch (err) {
      setContextError(err.message || "Failed to save context item");
    } finally {
      setIsSavingContext(false);
    }
  };

  const handleDeleteContextItem = async (contextId) => {
    if (!confirm("Are you sure you want to delete this context item?")) return;
    try {
      await taskService.deleteContext(contextId);
      await fetchTaskContexts();
      if (showInspector) {
        await handleInspectContext();
      }
    } catch (err) {
      alert(`Failed to delete context item: ${err.message}`);
    }
  };

  // Abort active streaming run
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRunning(false);
  };

  // Run Task Execution (Step 10 Orchestrator Pipeline)
  const handleExecuteTask = async (e) => {
    e?.preventDefault();
    if (!taskId) return;
    if (modelMode === "manual" && !selectedModel) {
      setExecutionError("Please select a target LLM model when in manual mode.");
      return;
    }

    if (!instructions.trim() && !task?.instructions && !task?.description) {
      setExecutionError("Task instructions cannot be empty. Please enter instructions before executing.");
      return;
    }

    // Auto-save any updated instructions/context_text first
    try {
      await taskService.updateTask(taskId, {
        title: title.trim(),
        instructions: instructions.trim(),
        context_text: contextText.trim() || null,
        model_mode: modelMode,
        preferred_model: modelMode === "manual" ? selectedModel : null,
      });
    } catch (err) {
      console.warn("Auto-save prior to run failed:", err);
    }

    setExecutionError(null);
    setFallbackEvent(null);
    setOutputStream("");
    setIsRunning(true);
    setPlanningState("analyzing");
    setCompletionEvaluation(null);
    setIterationCount(1);
    setRepairCount(0);
    setElapsedMs(0);
    setActiveRun(null);

    // Initial temporary steps placeholder
    if (executionPlan?.steps) {
      setLiveSteps(
        executionPlan.steps.map((st, idx) => ({
          id: st.id,
          step_index: idx + 1,
          step_type: st.type,
          status: "pending",
          tool_name: st.tool,
          retrieval_strategy: st.strategy,
          model: st.model,
        }))
      );
    } else {
      setLiveSteps([]);
    }

    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 50);

    const runPayload = {
      model: modelMode === "manual" ? selectedModel : undefined,
      model_mode: modelMode,
      preferred_model: modelMode === "manual" ? selectedModel : undefined,
      latency_preference: latencyPreference,
      cost_preference: costPreference,
      planner_mode: plannerMode,
      temperature: Number(temperature),
      max_context_tokens: Number(contextBudget),
      retrieval_mode: retrievalMode,
      retrieval_strategy: retrievalStrategy || undefined,
      retrieval_scope: retrievalScope,
      retrieval_top_k: Number(retrievalTopK),
      retrieval_project_scope: retrievalScope === "project",
      enable_web_search: enableWebSearch,
      web_search_query: webSearchQuery.trim() || undefined,
      web_search_limit: Number(webSearchLimit) || 5,
      web_search_recency_days: webSearchRecencyDays ? Number(webSearchRecencyDays) : undefined,
      tool_mode: enableWebSearch ? "enabled" : "disabled",
      tools_enabled: enableWebSearch ? ["web_search"] : [],
      evaluation_mode: evaluationMode,
      strict_evaluation: strictEvaluation,
      expected_format: expectedFormat || undefined,
    };

    if (enableStreaming) {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      let accumulated = "";
      await taskService.executeTaskStream(taskId, runPayload, {
        signal: controller.signal,
        onRunStart: (event) => {
          setActiveRun({
            id: event.run_id,
            task_id: taskId,
            status: "running",
            model_name: event.model || selectedModel,
            model_provider: event.provider,
            model_selection_reason: event.model_selection_reason,
            model_routing_policy: event.model_routing_policy,
            estimated_cost: event.estimated_cost,
            fallback_attempts: event.fallback_attempts,
            planner_mode: plannerMode,
            evaluation_mode: evaluationMode,
            evaluation_status: "running",
            context_item_count: event.context_item_count,
            estimated_context_tokens: event.estimated_context_tokens,
            context_truncated: event.context_truncated,
            retrieval_mode: retrievalMode,
            retrieval_required: event.retrieval_enabled,
            retrieval_enabled: event.retrieval_enabled,
            retrieval_strategy: event.retrieval_strategy,
            retrieval_scope: event.retrieval_scope,
            retrieval_confidence: event.retrieval_confidence,
            retrieval_reason: event.retrieval_reason,
            retrieved_chunk_count: event.retrieved_chunk_count,
            tools_used: event.tools_used || (enableWebSearch ? ["web_search"] : []),
            tool_call_count: event.tool_call_count,
            tool_latency_ms: event.tool_latency_ms,
            created_at: new Date().toISOString(),
          });
        },
        onModelSelected: (event) => {
          if (event.selection) {
            setModelPreview(event);
          }
        },
        onModelFallback: (event) => {
          setFallbackEvent(event);
        },
        onPlanningStart: (event) => {
          setPlanningState("analyzing");
          if (event.iteration) setIterationCount(event.iteration);
        },
        onPlanGenerated: (plan) => {
          setPlanningState(null);
          setExecutionPlan(plan);
          if (plan?.metadata?.repair_count !== undefined) {
            setRepairCount(plan.metadata.repair_count);
          }
          if (plan?.steps) {
            setLiveSteps(
              plan.steps.map((st, idx) => ({
                id: st.id,
                step_index: idx + 1,
                step_type: st.type,
                status: idx === 0 ? "running" : "pending",
                tool_name: st.tool,
                retrieval_strategy: st.strategy,
                model: st.model,
              }))
            );
          }
        },
        onStepStart: (stepRecord) => {
          setPlanningState(null);
          setLiveSteps((prev) => {
            const exists = prev.some((s) => s.id === stepRecord.id);
            if (exists) {
              return prev.map((s) =>
                s.id === stepRecord.id
                  ? { ...s, ...stepRecord, status: "running" }
                  : s
              );
            }
            return [...prev, { ...stepRecord, status: "running" }];
          });
        },
        onStepCompleted: (stepRecord) => {
          setLiveSteps((prev) =>
            prev.map((s) =>
              s.id === stepRecord.id
                ? { ...s, ...stepRecord, status: "completed" }
                : s
            )
          );
        },
        onStepFailed: (stepRecord) => {
          setLiveSteps((prev) =>
            prev.map((s) =>
              s.id === stepRecord.id
                ? { ...s, ...stepRecord, status: "failed" }
                : s
            )
          );
        },
        onEvaluating: () => {
          setPlanningState("evaluating");
        },
        onEvaluationCompleted: (evalData) => {
          setCompletionEvaluation(evalData);
          if (!evalData?.complete) {
            setPlanningState("replanning");
          } else {
            setPlanningState(null);
          }
        },
        onReplanGenerated: (plan, iter) => {
          setPlanningState(null);
          if (iter) setIterationCount(iter);
          setExecutionPlan(plan);
          if (plan?.steps) {
            setLiveSteps(
              plan.steps.map((st, idx) => ({
                id: st.id,
                step_index: idx + 1,
                step_type: st.type,
                status: idx === 0 ? "running" : "pending",
                tool_name: st.tool,
                retrieval_strategy: st.strategy,
                model: st.model,
              }))
            );
          }
        },
        onEvaluationStart: () => {
          setIsEvaluating(true);
          setEvaluationResult(null);
        },
        onEvaluationCheck: () => {},
        onEvaluationCompletedEvent: (evalData) => {
          setIsEvaluating(false);
          const res = evalData?.result || evalData;
          if (res?.checks || res?.status) {
            setEvaluationResult(res);
          }
        },
        onRevisionStart: (event) => {
          setIsRevising(true);
          if (event.attempt) setRevisionAttempts(event.attempt);
        },
        onRevisionCompleted: () => {
          setIsRevising(false);
        },
        onChunk: (delta) => {
          setPlanningState(null);
          accumulated += delta;
          setOutputStream(accumulated);
        },
        onRunCompleted: (completedRun) => {
          setPlanningState(null);
          setIsEvaluating(false);
          setIsRevising(false);
          setActiveRun(completedRun);
          if (completedRun.evaluation_result) {
            setEvaluationResult(completedRun.evaluation_result);
          }
          if (completedRun.revision_attempts !== undefined) {
            setRevisionAttempts(completedRun.revision_attempts);
          }
          if (completedRun.completion_evaluation) {
            setCompletionEvaluation(completedRun.completion_evaluation);
          }
          if (completedRun.repair_count !== undefined) {
            setRepairCount(completedRun.repair_count);
          }
          if (completedRun.iteration_count) {
            setIterationCount(completedRun.iteration_count);
          }
          if (completedRun.execution_plan) {
            setExecutionPlan(completedRun.execution_plan);
          }
          if (completedRun.execution_steps) {
            setLiveSteps(completedRun.execution_steps);
          }
          setOutputStream(completedRun.output_content || accumulated);
          fetchTaskRuns();
        },
        onError: (err) => {
          setPlanningState(null);
          setIsEvaluating(false);
          setIsRevising(false);
          clearInterval(timerRef.current);
          setIsRunning(false);
          setExecutionError(err.message || "Execution error encountered during task run.");
          fetchTaskRuns();
        },
        onComplete: () => {
          setPlanningState(null);
          setIsEvaluating(false);
          setIsRevising(false);
          clearInterval(timerRef.current);
          setIsRunning(false);
        },
      });
    } else {
      try {
        const completedRun = await taskService.executeTask(taskId, runPayload);
        setPlanningState(null);
        setIsEvaluating(false);
        setIsRevising(false);
        setActiveRun(completedRun);
        if (completedRun.evaluation_result) {
          setEvaluationResult(completedRun.evaluation_result);
        }
        if (completedRun.revision_attempts !== undefined) {
          setRevisionAttempts(completedRun.revision_attempts);
        }
        if (completedRun.completion_evaluation) {
          setCompletionEvaluation(completedRun.completion_evaluation);
        }
        if (completedRun.repair_count !== undefined) {
          setRepairCount(completedRun.repair_count);
        }
        if (completedRun.iteration_count) {
          setIterationCount(completedRun.iteration_count);
        }
        if (completedRun.execution_plan) {
          setExecutionPlan(completedRun.execution_plan);
        }
        if (completedRun.execution_steps) {
          setLiveSteps(completedRun.execution_steps);
        }
        setOutputStream(completedRun.output_content || "");
        await fetchTaskRuns();
      } catch (err) {
        setPlanningState(null);
        setIsEvaluating(false);
        setIsRevising(false);
        setExecutionError(err.message || "Failed to execute task.");
        await fetchTaskRuns();
      } finally {
        clearInterval(timerRef.current);
        setIsRunning(false);
      }
    }
  };

  const handleSelectPastRun = (run) => {
    setActiveRun(run);
    setOutputStream(run.output_content || "");
    setExecutionError(run.error_message || null);
    setPlanningState(null);
    setIsEvaluating(false);
    setIsRevising(false);
    if (run.evaluation_result) {
      setEvaluationResult(run.evaluation_result);
    } else {
      setEvaluationResult(null);
    }
    if (run.revision_attempts !== undefined) {
      setRevisionAttempts(run.revision_attempts);
    } else {
      setRevisionAttempts(0);
    }
    if (run.completion_evaluation) {
      setCompletionEvaluation(run.completion_evaluation);
    } else {
      setCompletionEvaluation(null);
    }
    if (run.repair_count !== undefined) {
      setRepairCount(run.repair_count);
    }
    if (run.iteration_count) {
      setIterationCount(run.iteration_count);
    }
    if (run.execution_plan) {
      setExecutionPlan(run.execution_plan);
    }
    if (run.execution_steps) {
      setLiveSteps(run.execution_steps);
    }
  };

  const handleCopy = () => {
    if (!outputStream) return;
    navigator.clipboard.writeText(outputStream);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStepDisplayName = (step) => {
    const type = step?.step_type || step?.type;
    switch (type) {
      case "retrieve":
        return `Search Project Knowledge (${step.retrieval_strategy || step.strategy || "Hybrid"})`;
      case "tool":
        if (step.tool_name === "web_search" || step.tool === "web_search") {
          return "Search Web";
        }
        return `Tool: ${step.tool_name || step.tool || "External Tool"}`;
      case "context":
        return "Assemble Context";
      case "generate":
        return `Generate Answer (${step.model || selectedModel || "LLM"})`;
      default:
        return type || "Step";
    }
  };

  const getStepIcon = (step) => {
    const type = step?.step_type || step?.type;
    switch (type) {
      case "retrieve":
        return <Search className="w-3.5 h-3.5 text-indigo-400" />;
      case "tool":
        return <Globe className="w-3.5 h-3.5 text-emerald-400" />;
      case "context":
        return <Layers className="w-3.5 h-3.5 text-purple-400" />;
      case "generate":
        return <Sparkles className="w-3.5 h-3.5 text-cyan-400" />;
      default:
        return <Workflow className="w-3.5 h-3.5 text-slate-400" />;
    }
  };


  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return <Badge variant="success" dot>Completed</Badge>;
      case "running":
        return <Badge variant="info" dot>Running</Badge>;
      case "queued":
        return <Badge variant="warning" dot>Queued</Badge>;
      case "failed":
        return <Badge variant="destructive" dot>Failed</Badge>;
      case "cancelled":
        return <Badge variant="outline">Cancelled</Badge>;
      case "active":
        return <Badge variant="info" dot>Active</Badge>;
      case "draft":
        return <Badge variant="warning" dot>Draft</Badge>;
      default:
        return <Badge variant="default">{status || "Unknown"}</Badge>;
    }
  };

  const getStrategyBadge = (strategy) => {
    switch (strategy?.toLowerCase()) {
      case "hybrid":
        return <Badge variant="success">Hybrid (Vector+KW)</Badge>;
      case "vector":
        return <Badge variant="info">Vector (Semantic)</Badge>;
      case "keyword":
        return <Badge variant="warning">Keyword (Exact)</Badge>;
      case "multi_query":
        return <Badge variant="purple" className="bg-purple-900/60 text-purple-200 border-purple-700">Multi-Query</Badge>;
      case "none":
        return <Badge variant="outline">None</Badge>;
      default:
        return <Badge variant="default">{strategy || "Inferred"}</Badge>;
    }
  };

  const getPriorityBadge = (priority) => {
    if (priority >= 90) return <Badge variant="destructive">Critical ({priority})</Badge>;
    if (priority >= 70) return <Badge variant="warning">High ({priority})</Badge>;
    if (priority >= 40) return <Badge variant="info">Medium ({priority})</Badge>;
    return <Badge variant="default">Low ({priority})</Badge>;
  };

  const estimateTokensLocal = (text) => {
    if (!text) return 0;
    return Math.max(Math.ceil(text.trim().length / 4), 1);
  };

  if (isLoadingTask) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] space-y-3">
        <Sparkles className="w-8 h-8 text-indigo-400 animate-spin" />
        <span className="text-sm text-slate-400">Loading task workspace...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-850">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link
              href="/app/tasks"
              className="inline-flex items-center gap-1 hover:text-indigo-400 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Tasks</span>
            </Link>
            <span>/</span>
            <span className="font-mono text-indigo-400">{taskId ? `${taskId.slice(0, 8)}...` : ""}</span>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Task Goal / Title"
              className="text-lg sm:text-xl font-bold bg-transparent text-white border-b border-transparent hover:border-slate-700 focus:border-indigo-500 focus:outline-none transition-colors px-1 py-0.5"
            />
            {getStatusBadge(taskStatus)}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={isSavingTask ? RefreshCw : Save}
            onClick={handleSaveTask}
            disabled={isSavingTask}
          >
            {isSavingTask ? "Saving..." : saveSuccess ? "Saved!" : "Save Task"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={RefreshCw}
            onClick={loadTaskAndContexts}
            disabled={isRunning}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Execution Error Banner */}
      {executionError && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-start gap-3 shadow-sm">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-rose-200">Execution Diagnostics</div>
            <div className="text-rose-300/90 leading-relaxed font-mono whitespace-pre-wrap">{executionError}</div>
          </div>
        </div>
      )}

      {/* Main Execution Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Task Definition, Context Items & Execution Parameters */}
        <div className="lg:col-span-5 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Task Specification</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Define the primary prompt and instructions sent to the AI Context Engine.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Instructions */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center justify-between">
                  <span>Task Instructions *</span>
                  <span className="text-[10px] text-indigo-400 font-normal">Primary Prompt</span>
                </label>
                <textarea
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="Explain exactly what the AI model must accomplish (e.g., 'What does our authentication implementation do?' or 'Summarize this paragraph')..."
                  rows={4}
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono leading-relaxed"
                  required
                />
              </div>

              {/* Task Background Context (Task Context Provider) */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center justify-between">
                  <span>Task Context (Baseline)</span>
                  <span className="text-[10px] text-slate-400 font-normal">TaskContextProvider</span>
                </label>
                <textarea
                  value={contextText}
                  onChange={(e) => setContextText(e.target.value)}
                  placeholder="Inherent background context (e.g. 'FastAPI backend using JWT authentication')..."
                  rows={2}
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono leading-relaxed"
                />
              </div>

              {/* Model & Budget Controls */}
              <div className="pt-2 border-t border-slate-800 space-y-3.5">
                {/* Step 12: Model Intelligence & Model Router Panel */}
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-indigo-500/25 space-y-3 shadow-inner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-indigo-400" />
                      <div>
                        <span className="text-xs font-semibold text-slate-100 block">
                          Model Intelligence & Router
                        </span>
                        <span className="text-[10px] text-slate-400 block">
                          Capability-based dynamic model selection & failover
                        </span>
                      </div>
                    </div>
                    {modelMode === "auto" && (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={handlePreviewModel}
                        disabled={isPreviewingModel}
                        className="text-[11px] text-indigo-300 hover:text-indigo-100"
                      >
                        {isPreviewingModel ? "Routing..." : "Preview Model"}
                      </Button>
                    )}
                  </div>

                  {/* Mode Selector: Automatic vs Choose Manually */}
                  <div className="space-y-1.5 pt-1">
                    <label className="text-[11px] font-medium text-slate-300 block">
                      Model Selection Mode:
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { id: "auto", label: "Automatic", desc: "Router selects best fit" },
                        { id: "manual", label: "Manual", desc: "Choose specific model" },
                      ].map((mode) => (
                        <label
                          key={mode.id}
                          className={`flex flex-col p-2 rounded-lg border cursor-pointer transition-all ${
                            modelMode === mode.id
                              ? "bg-indigo-950/70 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500/30"
                              : "bg-slate-900/90 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300"
                          }`}
                        >
                          <div className="flex items-center gap-1.5">
                            <input
                              type="radio"
                              name="model_mode_selector"
                              value={mode.id}
                              checked={modelMode === mode.id}
                              onChange={() => setModelMode(mode.id)}
                              className="accent-indigo-500"
                            />
                            <span className="text-xs font-semibold">{mode.label}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 pl-4 mt-0.5">{mode.desc}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Automatic Mode View */}
                  {modelMode === "auto" ? (
                    <div className="space-y-2.5 pt-2 border-t border-slate-800/80">
                      {/* Requirements Checklist Pills */}
                      <div className="space-y-1">
                        <label className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
                          Inferred Capability Requirements
                        </label>
                        <div className="flex flex-wrap gap-1.5">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-950/80 border border-indigo-500/30 text-indigo-300">
                            <Check className="w-3 h-3 text-emerald-400" /> Reasoning
                          </span>
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono border ${
                            enableStreaming
                              ? "bg-indigo-950/80 border-indigo-500/30 text-indigo-300"
                              : "bg-slate-900 border-slate-800 text-slate-500 line-through"
                          }`}>
                            <Check className="w-3 h-3 text-emerald-400" /> Streaming
                          </span>
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono border ${
                            enableWebSearch
                              ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-300"
                              : "bg-slate-900 border-slate-800 text-slate-500"
                          }`}>
                            {enableWebSearch ? <Check className="w-3 h-3 text-emerald-400" /> : <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />}
                            Tools {enableWebSearch ? "(Active)" : "(Optional)"}
                          </span>
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono border ${
                            contextBudget >= 8000
                              ? "bg-purple-950/80 border-purple-500/40 text-purple-300"
                              : "bg-slate-900 border-slate-800 text-slate-500"
                          }`}>
                            {contextBudget >= 8000 ? <Check className="w-3 h-3 text-purple-400" /> : <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />}
                            Long Context ({contextBudget >= 8000 ? "Required" : "Standard"})
                          </span>
                        </div>
                      </div>

                      {/* Policy Preferences Row */}
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Latency Preference</label>
                          <select
                            value={latencyPreference}
                            onChange={(e) => setLatencyPreference(e.target.value)}
                            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                          >
                            <option value="balanced">Balanced Latency</option>
                            <option value="low">Low Latency (Fast)</option>
                            <option value="high_quality">High Quality</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Cost Preference</label>
                          <select
                            value={costPreference}
                            onChange={(e) => setCostPreference(e.target.value)}
                            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                          >
                            <option value="balanced">Balanced Cost</option>
                            <option value="low">Low Cost (Economical)</option>
                            <option value="quality">Quality Focus</option>
                          </select>
                        </div>
                      </div>

                      {/* Live Model Preview Result */}
                      {modelPreview?.selection && (
                        <div className="p-2.5 rounded-lg bg-slate-900/95 border border-indigo-500/30 space-y-1.5 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] text-slate-400 font-mono">Proposed Model:</span>
                            <Badge variant="info" className="text-[10px] font-mono">
                              {modelPreview.selection.provider} / {modelPreview.selection.model}
                            </Badge>
                          </div>
                          {modelPreview.selection.reason && (
                            <p className="text-[11px] text-slate-300/90 leading-relaxed font-mono bg-slate-950/70 p-2 rounded border border-slate-800">
                              <span className="text-indigo-400 font-semibold">Selection Policy: </span>
                              {modelPreview.selection.reason}
                            </p>
                          )}
                        </div>
                      )}

                      {modelPreviewError && (
                        <div className="p-2 rounded bg-rose-950/60 border border-rose-800 text-rose-300 text-[10px]">
                          {modelPreviewError}
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Manual Mode View: List Only Enabled Server-Approved Models */
                    <div className="space-y-2 pt-2 border-t border-slate-800/80">
                      <div>
                        <label className="text-[11px] font-medium text-slate-300 block mb-1">
                          Select Allowed Model
                        </label>
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
                        >
                          {models.filter((m) => m.enabled !== false && m.is_enabled !== false).map((m) => (
                            <option key={m.id || m.model_id} value={m.id || m.model_id}>
                              {m.display_name || m.name || m.model_id} ({m.provider})
                            </option>
                          ))}
                          {models.length === 0 && (
                            <option value="" disabled>
                              Loading registered models...
                            </option>
                          )}
                        </select>
                      </div>

                      {/* Selected Model Capabilities Badges */}
                      {(() => {
                        const cur = models.find((m) => (m.id || m.model_id) === selectedModel);
                        if (!cur) return null;
                        return (
                          <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1.5">
                            <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                              <span className="text-slate-400">Context: <strong className="text-indigo-300">{cur.context_window?.toLocaleString() || "128k"}</strong></span>
                              <span>•</span>
                              <span className="text-slate-400">Latency: <strong className="text-emerald-300">{cur.latency_class || "balanced"}</strong></span>
                              <span>•</span>
                              <span className="text-slate-400">Cost: <strong className="text-amber-300">{cur.cost_class || "balanced"}</strong></span>
                            </div>
                            <div className="flex flex-wrap gap-1 pt-1">
                              {cur.capabilities?.map((cap) => (
                                <span key={cap} className="px-1.5 py-0.2 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[9px] font-mono">
                                  {cap}
                                </span>
                              ))}
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  )}
                </div>

                {/* Temperature & Budget row */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium text-slate-300">Temperature</span>
                      <span className="font-mono text-indigo-400 font-semibold">{temperature}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium text-slate-300">Context Budget</span>
                      <span className="font-mono text-indigo-400 font-semibold">{contextBudget} tok</span>
                    </div>
                    <select
                      value={contextBudget}
                      onChange={(e) => setContextBudget(Number(e.target.value))}
                      className="w-full rounded-lg bg-slate-900 border border-slate-700 px-2 py-1 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
                    >
                      <option value={2000}>2k tokens</option>
                      <option value={4000}>4k tokens</option>
                      <option value={8000}>8k tokens</option>
                      <option value={16000}>16k tokens</option>
                    </select>
                  </div>
                </div>

                {/* Step 8: Intelligent Retrieval Router Panel */}
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-indigo-500/25 space-y-3 shadow-inner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 text-indigo-400" />
                      <div>
                        <span className="text-xs font-semibold text-slate-100 block">
                          Retrieval Router
                        </span>
                        <span className="text-[10px] text-slate-400 block">
                          Knowledge grounding & strategy orchestration
                        </span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={handlePreviewRetrieval}
                      disabled={isPreviewingRetrieval}
                      className="text-[11px] text-indigo-300 hover:text-indigo-100"
                    >
                      {isPreviewingRetrieval ? "Routing..." : "Preview Decision"}
                    </Button>
                  </div>

                  {/* Retrieval Mode Radio Group */}
                  <div className="space-y-1.5 pt-1">
                    <label className="text-[11px] font-medium text-slate-300 block">
                      Retrieval Mode:
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { id: "auto", label: "Automatic", desc: "Router decides" },
                        { id: "always", label: "Always", desc: "Force retrieval" },
                        { id: "never", label: "Never", desc: "No retrieval" },
                      ].map((mode) => (
                        <label
                          key={mode.id}
                          className={`flex flex-col p-2 rounded-lg border cursor-pointer transition-all ${
                            retrievalMode === mode.id
                              ? "bg-indigo-950/70 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500/30"
                              : "bg-slate-900/90 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300"
                          }`}
                        >
                          <div className="flex items-center gap-1.5">
                            <input
                              type="radio"
                              name="retrieval_mode_selector"
                              value={mode.id}
                              checked={retrievalMode === mode.id}
                              onChange={() => setRetrievalMode(mode.id)}
                              className="accent-indigo-500"
                            />
                            <span className="text-xs font-semibold">{mode.label}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 pl-4 mt-0.5">{mode.desc}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Collapsible Advanced Retrieval Options */}
                  {retrievalMode !== "never" && (
                    <div className="pt-2 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={() => setShowAdvancedRetrieval(!showAdvancedRetrieval)}
                        className="flex items-center justify-between w-full text-[11px] text-slate-400 hover:text-slate-200 transition-colors py-0.5"
                      >
                        <span className="flex items-center gap-1.5 font-medium">
                          <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Advanced Routing Options</span>
                        </span>
                        {showAdvancedRetrieval ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>

                      {showAdvancedRetrieval && (
                        <div className="space-y-3 pt-2.5">
                          {/* Strategy Override */}
                          <div>
                            <label className="text-[11px] text-slate-300 block mb-1">
                              Strategy Override
                            </label>
                            <select
                              value={retrievalStrategy}
                              onChange={(e) => setRetrievalStrategy(e.target.value)}
                              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
                            >
                              <option value="">Auto / Inferred by Router</option>
                              <option value="hybrid">Hybrid (Vector + BM25 Keyword)</option>
                              <option value="vector">Vector (Semantic Embedding)</option>
                              <option value="keyword">Keyword (Exact BM25 Match)</option>
                              <option value="multi_query">Multi-Query (Query Expansion)</option>
                            </select>
                          </div>

                          {/* Scope Override */}
                          <div>
                            <label className="text-[11px] text-slate-300 block mb-1">
                              Retrieval Scope Boundary
                            </label>
                            <div className="grid grid-cols-2 gap-2">
                              <button
                                type="button"
                                onClick={() => setRetrievalScope("project")}
                                className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-medium border text-center transition-colors ${
                                  retrievalScope === "project"
                                    ? "bg-indigo-950/60 border-indigo-500/50 text-indigo-200"
                                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-300"
                                }`}
                              >
                                Project Scope
                              </button>
                              <button
                                type="button"
                                onClick={() => setRetrievalScope("workspace")}
                                className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-medium border text-center transition-colors ${
                                  retrievalScope === "workspace"
                                    ? "bg-indigo-950/60 border-indigo-500/50 text-indigo-200"
                                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-300"
                                }`}
                              >
                                Workspace Scope
                              </button>
                            </div>
                          </div>

                          {/* Top K Results */}
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] text-slate-300">Candidate Top-K</span>
                            <div className="flex items-center gap-1 font-mono">
                              {[4, 8, 12, 16, 24].map((num) => (
                                <button
                                  key={num}
                                  type="button"
                                  onClick={() => setRetrievalTopK(num)}
                                  className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                                    retrievalTopK === num
                                      ? "bg-indigo-600 text-white"
                                      : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                                  }`}
                                >
                                  {num}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Router Preview Live Result Card */}
                  {previewDecision && (
                    <div className="p-3 rounded-lg bg-slate-900/90 border border-indigo-500/30 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                          <Compass className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Router Decision Preview</span>
                        </div>
                        {previewDecision.retrieval_required ? (
                          <Badge variant="success">Required</Badge>
                        ) : (
                          <Badge variant="outline">Not Required</Badge>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-2 font-mono text-[11px] pt-1 border-t border-slate-800">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Strategy</span>
                          <strong className="text-indigo-300">{previewDecision.strategy}</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Scope</span>
                          <strong className="text-purple-300">{previewDecision.scope}</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Confidence</span>
                          <strong className="text-emerald-300">
                            {Math.round((previewDecision.confidence || 1.0) * 100)}%
                          </strong>
                        </div>
                      </div>

                      {previewDecision.reason && (
                        <p className="text-[11px] text-slate-300/90 leading-relaxed font-mono bg-slate-950/60 p-2 rounded border border-slate-800/80">
                          <span className="text-indigo-400 font-semibold">Why: </span>
                          {previewDecision.reason}
                        </p>
                      )}
                    </div>
                  )}

                  {previewError && (
                    <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-[11px]">
                      {previewError}
                    </div>
                  )}
                </div>

                {/* Step 9: Tools & External Grounding */}
                <div className="space-y-3 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-semibold text-slate-200">Tools & External Grounding</span>
                    </div>
                    {enableWebSearch && (
                      <Badge variant="success" className="text-[10px]">Active</Badge>
                    )}
                  </div>

                  {/* Web Search Tool Toggle */}
                  <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
                    <label className="flex items-start gap-3 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={enableWebSearch}
                        onChange={(e) => setEnableWebSearch(e.target.checked)}
                        className="mt-0.5 w-4 h-4 accent-emerald-500 rounded cursor-pointer"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Globe className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-xs font-semibold text-slate-200">Web Search Tool</span>
                          <span className="text-[10px] px-1.5 py-0.2 bg-emerald-950/60 border border-emerald-800/40 text-emerald-300 rounded font-mono">
                            live web
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                          Query live internet sources and feed normalized results as untrusted external context.
                        </p>
                      </div>
                    </label>

                    {/* Collapsible Web Search Settings */}
                    {enableWebSearch && (
                      <div className="pt-3 border-t border-slate-800 space-y-3 text-xs animate-in fade-in duration-200">
                        <div>
                          <label className="text-[11px] font-medium text-slate-300 block mb-1">
                            Search Query Override (Optional)
                          </label>
                          <input
                            type="text"
                            value={webSearchQuery}
                            onChange={(e) => setWebSearchQuery(e.target.value)}
                            placeholder="Defaults to task title & instructions..."
                            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <span className="text-[10px] text-slate-400 block mb-1">Result Limit</span>
                            <div className="flex items-center gap-1 font-mono">
                              {[3, 5, 8, 10].map((num) => (
                                <button
                                  key={num}
                                  type="button"
                                  onClick={() => setWebSearchLimit(num)}
                                  className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                                    webSearchLimit === num
                                      ? "bg-emerald-600 text-white"
                                      : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                                  }`}
                                >
                                  {num}
                                </button>
                              ))}
                            </div>
                          </div>

                          <div>
                            <span className="text-[10px] text-slate-400 block mb-1">Recency Filter</span>
                            <select
                              value={webSearchRecencyDays}
                              onChange={(e) => setWebSearchRecencyDays(e.target.value)}
                              className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300 focus:outline-none focus:border-emerald-500 font-mono"
                            >
                              <option value="">Any Time</option>
                              <option value="1">Past 24 Hours</option>
                              <option value="7">Past 7 Days</option>
                              <option value="30">Past 30 Days</option>
                              <option value="365">Past Year</option>
                            </select>
                          </div>
                        </div>

                        <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80 text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          <span>Results marked as untrusted external content for prompt-injection safety.</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Step 10 & 11: Execution Plan & Planning Mode Card */}
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-indigo-500/25 space-y-3 shadow-inner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Workflow className="w-4 h-4 text-cyan-400" />
                      <div>
                        <span className="text-xs font-semibold text-slate-100 block">
                          Execution Plan & Planner
                        </span>
                        <span className="text-[10px] text-slate-400 block">
                          LLM-assisted planning & execution bounds
                        </span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={handlePreviewPlan}
                      disabled={isLoadingPlan}
                      className="text-[11px] text-cyan-300 hover:text-cyan-100"
                    >
                      {isLoadingPlan ? "Planning..." : executionPlan ? "Refresh Plan" : "Preview Plan"}
                    </Button>
                  </div>

                  {/* Planning Mode Selector (Step 11) */}
                  <div className="space-y-1.5 pt-1">
                    <label className="text-[11px] font-medium text-slate-300 block">
                      Planning Mode:
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { id: "hybrid", label: "Automatic", desc: "Hybrid LLM + Baseline" },
                        { id: "deterministic", label: "Deterministic", desc: "Rule-based Pipeline" },
                        { id: "llm", label: "LLM-Assisted", desc: "Structured + Validation" },
                      ].map((mode) => (
                        <label
                          key={mode.id}
                          className={`flex flex-col p-2 rounded-lg border cursor-pointer transition-all ${
                            plannerMode === mode.id
                              ? "bg-cyan-950/70 border-cyan-500 text-white shadow-sm ring-1 ring-cyan-500/30"
                              : "bg-slate-900/90 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300"
                          }`}
                        >
                          <div className="flex items-center gap-1.5">
                            <input
                              type="radio"
                              name="planner_mode_selector"
                              value={mode.id}
                              checked={plannerMode === mode.id}
                              onChange={() => setPlannerMode(mode.id)}
                              className="accent-cyan-500"
                            />
                            <span className="text-xs font-semibold">{mode.label}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 pl-4 mt-0.5 leading-tight">{mode.desc}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {executionPlan && (
                    <div className="space-y-2 pt-1 border-t border-slate-800/80">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 pb-1 border-b border-slate-800">
                        <span>
                          Planned Steps: <strong className="text-white font-mono">{executionPlan.steps?.length || 0}</strong>
                        </span>
                        <div className="flex items-center gap-1.5 font-mono text-[10px]">
                          {executionPlan.metadata?.planner_mode && (
                            <Badge variant="outline" className="text-[9px] capitalize text-cyan-300">
                              {executionPlan.metadata.planner_mode}
                            </Badge>
                          )}
                          {executionPlan.metadata?.repair_count > 0 && (
                            <Badge variant="warning" className="text-[9px]">
                              {executionPlan.metadata.repair_count} repair
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        {executionPlan.steps?.map((step, idx) => (
                          <div
                            key={step.id || idx}
                            className="p-2 rounded-lg bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-2 text-xs"
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="font-mono text-cyan-400 font-bold text-[11px]">
                                {idx + 1}.
                              </span>
                              {getStepIcon(step)}
                              <span className="font-medium text-slate-200 truncate">
                                {getStepDisplayName(step)}
                              </span>
                            </div>
                            <div className="shrink-0 flex items-center gap-1">
                              <Badge variant="outline" className="text-[10px] capitalize font-mono">
                                {step.type}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {planError && (
                    <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-[11px]">
                      {planError}
                    </div>
                  )}
                </div>

                {/* SSE Streaming Toggle */}
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-xs">
                    <span className="font-medium text-slate-200 block">Server-Sent Events Streaming</span>
                    <span className="text-[10px] text-slate-400">Stream tokens in real-time</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={enableStreaming}
                    onChange={(e) => setEnableStreaming(e.target.checked)}
                    className="w-4 h-4 accent-indigo-500 rounded cursor-pointer"
                  />
                </div>

                {/* Step 13: Evaluation & Verification Policy Panel */}
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-emerald-500/25 space-y-3 shadow-inner">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <div>
                        <span className="text-xs font-semibold text-slate-100 block">
                          Verification & Evaluation
                        </span>
                        <span className="text-[10px] text-slate-400 block">
                          Quality, grounding, completeness & format checks
                        </span>
                      </div>
                    </div>
                    {outputStream && !isRunning && (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={handleManualEvaluate}
                        disabled={isEvaluating}
                        className="text-[11px] text-emerald-300 hover:text-emerald-100"
                      >
                        {isEvaluating ? "Verifying..." : "Evaluate Output"}
                      </Button>
                    )}
                  </div>

                  {/* Evaluation Policy Mode */}
                  <div className="space-y-1.5 pt-1">
                    <label className="text-[11px] font-medium text-slate-300 block">
                      Verification Policy:
                    </label>
                    <div className="grid grid-cols-4 gap-1.5">
                      {[
                        { id: "standard", label: "Standard", desc: "Balanced" },
                        { id: "strict", label: "Strict", desc: "No warnings" },
                        { id: "basic", label: "Basic", desc: "Fast checks" },
                        { id: "off", label: "Off", desc: "Disabled" },
                      ].map((mode) => (
                        <label
                          key={mode.id}
                          className={`flex flex-col p-1.5 rounded-lg border cursor-pointer transition-all text-center ${
                            evaluationMode === mode.id
                              ? "bg-emerald-950/70 border-emerald-500 text-white shadow-sm ring-1 ring-emerald-500/30"
                              : "bg-slate-900/90 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300"
                          }`}
                        >
                          <input
                            type="radio"
                            name="evaluation_mode_selector"
                            value={mode.id}
                            checked={evaluationMode === mode.id}
                            onChange={() => setEvaluationMode(mode.id)}
                            className="sr-only"
                          />
                          <span className="text-[11px] font-semibold">{mode.label}</span>
                          <span className="text-[9px] text-slate-400 mt-0.5">{mode.desc}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Expected Output Format Dropdown */}
                  {evaluationMode !== "off" && (
                    <div className="space-y-2 pt-1 border-t border-slate-800/80">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Expected Format</label>
                          <select
                            value={expectedFormat}
                            onChange={(e) => setExpectedFormat(e.target.value)}
                            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
                          >
                            <option value="">Auto / Unspecified</option>
                            <option value="json">JSON Object/Array</option>
                            <option value="markdown">Markdown</option>
                            <option value="bullet_list">Bullet List</option>
                            <option value="table">Table Format</option>
                            <option value="code">Code Block</option>
                          </select>
                        </div>
                        <div className="flex flex-col justify-end">
                          <label className="flex items-center gap-2 text-[11px] text-slate-300 cursor-pointer select-none pb-1">
                            <input
                              type="checkbox"
                              checked={strictEvaluation}
                              onChange={(e) => setStrictEvaluation(e.target.checked)}
                              className="w-3.5 h-3.5 accent-emerald-500 rounded cursor-pointer"
                            />
                            <span>Strict Verification</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Execution Action Button */}
              <div className="pt-2 flex gap-2">
                {isRunning ? (
                  <Button
                    variant="destructive"
                    size="md"
                    icon={Square}
                    onClick={handleStop}
                    className="w-full"
                  >
                    Stop Execution
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="md"
                    icon={Play}
                    onClick={handleExecuteTask}
                    disabled={(!instructions.trim() && !task?.instructions) || !selectedModel}
                    className="w-full shadow-md shadow-indigo-900/30"
                  >
                    Run Task with Orchestrator
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>


          {/* Context Management Section (Step 6) */}
          <Card>
            <CardHeader className="py-3 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <div>
                  <CardTitle className="text-sm">Context Management</CardTitle>
                  <CardDescription className="text-[11px]">
                    {contexts.length} explicit item{contexts.length !== 1 ? "s" : ""} configured
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="xs"
                  icon={Eye}
                  onClick={handleInspectContext}
                  disabled={isLoadingInspect}
                >
                  {isLoadingInspect ? "Inspecting..." : "Inspect Context"}
                </Button>
                <Button
                  variant="primary"
                  size="xs"
                  icon={Plus}
                  onClick={handleOpenAddContextModal}
                >
                  Add Context
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {isLoadingContexts ? (
                <div className="p-6 text-center text-xs text-slate-400">Loading context items...</div>
              ) : (
                <div className="divide-y divide-slate-850">
                  {/* Task Baseline Context Preview */}
                  {contextText && (
                    <div className="p-3 bg-slate-900/40 flex items-start justify-between gap-3">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-200">Task Context</span>
                          <Badge variant="outline">task</Badge>
                          <Badge variant="warning">Priority 80</Badge>
                          <span className="text-[10px] font-mono text-slate-400">
                            ~{estimateTokensLocal(contextText)} tok
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 line-clamp-2 font-mono">
                          {contextText}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Manual Context Items */}
                  {contexts.length === 0 && !contextText ? (
                    <div className="p-6 text-center space-y-2">
                      <Database className="w-6 h-6 text-slate-600 mx-auto" />
                      <p className="text-xs text-slate-400">
                        No context items yet. Add manual context documents, API specs, or constraints to empower LLM execution.
                      </p>
                      <Button
                        variant="outline"
                        size="xs"
                        icon={Plus}
                        onClick={handleOpenAddContextModal}
                        className="mt-2"
                      >
                        Add First Context Item
                      </Button>
                    </div>
                  ) : (
                    contexts.map((ctx) => (
                      <div
                        key={ctx.id}
                        className="p-3.5 hover:bg-slate-850/40 transition-colors flex items-start justify-between gap-3"
                      >
                        <div className="space-y-1 flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-semibold text-slate-200 truncate">
                              {ctx.title}
                            </span>
                            <Badge variant="outline">{ctx.source_type || "manual"}</Badge>
                            {getPriorityBadge(ctx.priority)}
                            <span className="text-[10px] font-mono text-indigo-400">
                              ~{ctx.estimated_tokens || estimateTokensLocal(ctx.content)} tok
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 line-clamp-2 font-mono leading-relaxed">
                            {ctx.content}
                          </p>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() => handleOpenEditContextModal(ctx)}
                            className="p-1 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded transition-colors"
                            title="Edit context item"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteContextItem(ctx.id)}
                            className="p-1 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors"
                            title="Delete context item"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: AI Output & Live Telemetry + Context Inspector View */}
        <div className="lg:col-span-7 space-y-4">
          {/* AI Execution Output */}
          <Card className="flex flex-col min-h-[500px]">
            <CardHeader className="py-3 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <div>
                  <CardTitle className="text-sm">AI Execution Output</CardTitle>
                  <div className="flex items-center gap-2 mt-0.5">
                    {activeRun && (
                      <span className="font-mono text-[10px] text-indigo-400">
                        Run: {activeRun.id.slice(0, 8)}...
                      </span>
                    )}
                    {getStatusBadge(isRunning ? "running" : activeRun?.status)}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {elapsedMs > 0 && isRunning && (
                  <span className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                    <Clock className="w-3 h-3 text-indigo-400" />
                    {(elapsedMs / 1000).toFixed(2)}s
                  </span>
                )}
                {outputStream && (
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={copied ? Check : Copy}
                    onClick={handleCopy}
                    className="text-xs py-1 h-7"
                  >
                    {copied ? "Copied" : "Copy"}
                  </Button>
                )}
              </div>
            </CardHeader>

            {/* Live Response Content Viewport */}
            <CardContent className="flex-1 p-4 bg-slate-950/90 font-mono text-xs overflow-y-auto flex flex-col justify-between">
              {/* Step 12: Live Provider Failover Banner */}
              {(fallbackEvent || (activeRun?.fallback_attempts && activeRun.fallback_attempts.length > 0)) && (
                <div className="mb-3.5 p-3.5 rounded-xl bg-amber-950/70 border border-amber-500/50 text-amber-200 text-xs font-mono space-y-1 shadow-md shadow-amber-950/40">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-semibold text-amber-300">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>Provider Failover Activated</span>
                    </div>
                    <Badge variant="warning" className="text-[10px]">
                      Fallback Attempt {fallbackEvent?.attempt || activeRun?.fallback_attempts?.length || 1}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-amber-200/90 leading-relaxed pt-0.5">
                    Primary candidate failed
                    {fallbackEvent?.error_message ? ` (${fallbackEvent.error_message})` : ""}.
                    Successfully routed failover to{" "}
                    <strong className="text-white font-semibold">{fallbackEvent?.fallback_model || activeRun?.final_model || activeRun?.model_name}</strong>
                    {" "}({fallbackEvent?.provider || activeRun?.model_provider || "fallback provider"}).
                  </p>
                </div>
              )}

              {/* Step 11: Live Planning Banner */}
              {isRunning && planningState === "analyzing" && (
                <div className="mb-3.5 p-3.5 rounded-xl bg-indigo-950/80 border border-indigo-500/40 flex items-center justify-between shadow-lg shadow-indigo-950/50 animate-pulse">
                  <div className="flex items-center gap-2.5 text-indigo-200 text-xs font-semibold">
                    <Sparkles className="w-4 h-4 text-indigo-400 animate-spin" />
                    <span>Analyzing task & synthesizing execution plan...</span>
                  </div>
                  <Badge variant="warning" className="text-[10px]">
                    Planning (Iter {iterationCount})
                  </Badge>
                </div>
              )}

              {/* Step 11: Live Evidence Evaluation Card */}
              {(planningState === "evaluating" || completionEvaluation) && (
                <div className={`mb-3.5 p-3 rounded-xl border text-xs font-mono space-y-1.5 ${
                  completionEvaluation?.complete
                    ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
                    : "bg-amber-950/40 border-amber-500/40 text-amber-200"
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-semibold">
                      {completionEvaluation?.complete ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                      )}
                      <span>Evidence Evaluation (Iteration {iterationCount})</span>
                    </div>
                    {planningState === "evaluating" ? (
                      <Badge variant="info" dot>Evaluating Evidence</Badge>
                    ) : completionEvaluation?.complete ? (
                      <Badge variant="success">Evidence Complete</Badge>
                    ) : (
                      <Badge variant="warning">Missing Info • Re-planning</Badge>
                    )}
                  </div>
                  {completionEvaluation?.reason && (
                    <p className="text-[11px] text-slate-300 leading-relaxed font-mono">
                      <span className="text-slate-200 font-semibold">Evaluation: </span>
                      {completionEvaluation.reason}
                    </p>
                  )}
                  {completionEvaluation?.missing_information?.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[10px] text-amber-400 font-semibold">Missing:</span>
                      {completionEvaluation.missing_information.map((item, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-amber-950/80 border border-amber-800/60 text-amber-300 text-[10px]">
                          {item}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Step 10 & 11: Orchestration Execution Step Tracker */}
              {(isRunning || (liveSteps && liveSteps.length > 0)) && (
                <div className="mb-4 p-3.5 rounded-xl bg-slate-900/90 border border-indigo-500/30 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 font-semibold text-slate-200 text-xs">
                      <Workflow className="w-4 h-4 text-cyan-400" />
                      <span>Execution Plan</span>
                      <Badge variant="outline" className="text-[10px] capitalize text-cyan-300 border-cyan-800/40 font-mono">
                        {activeRun?.planner_mode || plannerMode}
                      </Badge>
                      {iterationCount > 1 && (
                        <Badge variant="purple" className="text-[10px] bg-purple-950 text-purple-300 border-purple-800 font-mono">
                          Iter {iterationCount}
                        </Badge>
                      )}
                      {repairCount > 0 && (
                        <Badge variant="warning" className="text-[10px] font-mono">
                          {repairCount} repair
                        </Badge>
                      )}
                      {isRunning ? (
                        <Badge variant="info" dot>Running</Badge>
                      ) : activeRun?.failed_step ? (
                        <Badge variant="destructive" dot>Failed at {activeRun.failed_step}</Badge>
                      ) : (
                        <Badge variant="success" dot>Completed</Badge>
                      )}
                    </div>
                    {activeRun?.orchestration_duration_ms ? (
                      <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                        Orchestration: {activeRun.orchestration_duration_ms}ms
                      </span>
                    ) : null}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1">
                    {liveSteps.map((step, idx) => {
                      const isRunningStep = isRunning && step.status === "running";
                      const isCompletedStep = step.status === "completed";
                      const isFailedStep = step.status === "failed";

                      let statusIcon = <Clock className="w-3.5 h-3.5 text-slate-500" />;
                      let cardBg = "bg-slate-950/80 border-slate-800 text-slate-400";

                      if (isRunningStep) {
                        statusIcon = <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />;
                        cardBg = "bg-indigo-950/60 border-indigo-500/60 text-indigo-200 shadow-sm ring-1 ring-indigo-500/20";
                      } else if (isCompletedStep) {
                        statusIcon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
                        cardBg = "bg-emerald-950/30 border-emerald-800/50 text-emerald-200";
                      } else if (isFailedStep) {
                        statusIcon = <XCircle className="w-3.5 h-3.5 text-rose-400" />;
                        cardBg = "bg-rose-950/40 border-rose-800/60 text-rose-200";
                      }

                      return (
                        <div
                          key={step.id || idx}
                          className={`p-2.5 rounded-lg border text-xs font-mono flex items-start gap-2.5 transition-all ${cardBg}`}
                        >
                          <span className="shrink-0 mt-0.5">{statusIcon}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-1">
                              <span className="font-semibold truncate">
                                {getStepDisplayName(step)}
                              </span>
                              {step.duration_ms !== null && step.duration_ms !== undefined && (
                                <span className="text-[10px] text-slate-400 shrink-0">
                                  {step.duration_ms}ms
                                </span>
                              )}
                            </div>
                            {step.error_message && (
                              <p className="text-[10px] text-rose-400 mt-1 line-clamp-2">
                                {step.error_message}
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {outputStream ? (
                <div className="text-slate-100 whitespace-pre-wrap leading-relaxed">
                  {outputStream}
                  {isRunning && (
                    <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse align-middle" />
                  )}
                </div>
              ) : isRunning ? (
                <div className="flex flex-col items-center justify-center flex-1 py-16 text-slate-400 space-y-3">
                  <Sparkles className="w-7 h-7 text-indigo-400 animate-spin" />
                  <span className="text-xs">Orchestrating context & invoking {selectedModel}...</span>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center flex-1 py-16 text-slate-500 space-y-2">
                  <Terminal className="w-8 h-8 text-slate-700" />
                  <span className="text-xs">Click &apos;Run Task with Orchestrator&apos; to execute this task</span>
                </div>
              )}


              {/* Step 8: Retrieval Decision Observability Panel */}
              {activeRun && (
                <div className="mt-4 p-3.5 rounded-xl bg-slate-900/90 border border-indigo-500/30 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800 text-xs">
                    <div className="flex items-center gap-2 font-semibold text-slate-200">
                      <Network className="w-4 h-4 text-indigo-400" />
                      <span>Retrieval Decision:</span>
                      {activeRun.retrieval_required || activeRun.retrieval_enabled ? (
                        <Badge variant="success">Used</Badge>
                      ) : (
                        <Badge variant="outline">Not required</Badge>
                      )}
                    </div>

                    {(activeRun.retrieval_required || activeRun.retrieval_enabled) && (
                      <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
                        <span>Strategy: <strong className="text-indigo-300">{activeRun.retrieval_strategy || "Hybrid"}</strong></span>
                        <span>• Scope: <strong className="text-purple-300">{activeRun.retrieval_scope || "Project"}</strong></span>
                        <span>• Sources: <strong className="text-cyan-300">{activeRun.retrieved_chunk_count || activeRun.retrieval_sources?.length || 0}</strong></span>
                        {activeRun.retrieval_confidence !== null && activeRun.retrieval_confidence !== undefined && (
                          <span>• Conf: <strong className="text-emerald-300">{Math.round(activeRun.retrieval_confidence * 100)}%</strong></span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Why retrieval? Explanation Card */}
                  {activeRun.retrieval_reason && (
                    <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 flex items-start gap-2">
                      <HelpCircle className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-indigo-300">Why retrieval: </span>
                        <span>{activeRun.retrieval_reason}</span>
                      </div>
                    </div>
                  )}

                  {/* Step 9: Web Search Grounded Sources */}
                  {(() => {
                    const webSources = activeRun.input_snapshot?.web_sources || [];
                    const hasWebTool = activeRun.tools_used?.includes("web_search") || activeRun.context_sources?.includes("web");
                    if (!hasWebTool && webSources.length === 0) return null;

                    return (
                      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-emerald-500/30 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 font-semibold text-slate-200 text-xs">
                            <Globe className="w-4 h-4 text-emerald-400" />
                            <span>Web Search Grounded Sources</span>
                            <Badge variant="success" className="text-[10px]">
                              {webSources.length > 0 ? `${webSources.length} sources` : "Active"}
                            </Badge>
                          </div>
                          {activeRun.tool_latency_ms !== null && activeRun.tool_latency_ms !== undefined && (
                            <span className="text-[10px] font-mono text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                              Tool Latency: {activeRun.tool_latency_ms}ms
                            </span>
                          )}
                        </div>

                        {webSources.length > 0 ? (
                          <div className="space-y-2 pt-1">
                            {webSources.map((src, idx) => (
                              <div
                                key={src.url || idx}
                                className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1.5 text-xs"
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex items-center gap-2 min-w-0">
                                    <span className="font-mono text-emerald-400 font-bold text-[11px]">
                                      {idx + 1}.
                                    </span>
                                    {src.url ? (
                                      <a
                                        href={src.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="font-medium text-slate-100 hover:text-emerald-300 underline underline-offset-2 flex items-center gap-1 truncate"
                                      >
                                        <span className="truncate">{src.title || src.url}</span>
                                        <ExternalLink className="w-3 h-3 shrink-0 text-slate-400" />
                                      </a>
                                    ) : (
                                      <span className="font-medium text-slate-100 truncate">{src.title}</span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-1.5 shrink-0">
                                    {src.source && (
                                      <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[10px] font-mono">
                                        {src.source}
                                      </span>
                                    )}
                                    {src.published_at && (
                                      <span className="text-[10px] text-slate-400 font-mono">
                                        {src.published_at}
                                      </span>
                                    )}
                                  </div>
                                </div>
                                {src.snippet && (
                                  <p className="text-slate-400 text-[11px] line-clamp-2 font-mono leading-relaxed pl-4 border-l border-emerald-800/40">
                                    {src.snippet.replace(/^\[EXTERNAL UNTRUSTED WEB CONTENT[^\]]*\]\s*/i, "").replace(/^Source URL:[^\n]*\n+/i, "").replace(/^Published Date:[^\n]*\n+/i, "")}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-[11px] text-slate-400 font-mono">
                            Web search was executed during this run.
                          </p>
                        )}
                      </div>
                    );
                  })()}

                  {/* Retrieved Sources list */}
                  {activeRun.retrieval_sources && activeRun.retrieval_sources.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[11px] font-semibold text-slate-300 block">
                        Grounded Sources ({activeRun.retrieval_sources.length})
                      </span>
                      {activeRun.retrieval_sources.map((src, idx) => (
                        <div
                          key={src.chunk_id || idx}
                          className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between gap-3 text-xs"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <span className="font-mono text-indigo-400 font-bold text-[11px]">
                              {idx + 1}.
                            </span>
                            <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                            <div className="truncate">
                              <span className="font-medium text-slate-100">{src.filename}</span>
                              {src.page_number && (
                                <span className="text-[11px] text-slate-400 ml-2 font-mono">
                                  • Page {src.page_number}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-2 font-mono text-[11px] shrink-0">
                            {src.score !== null && src.score !== undefined && (
                              <span className="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/20 text-indigo-300">
                                Relevance: {(src.score * 100).toFixed(0)}%
                              </span>
                            )}
                            {src.vector_score !== null && src.vector_score !== undefined && (
                              <span className="px-1.5 py-0.5 rounded bg-purple-950/40 border border-purple-800/30 text-purple-300 text-[10px] hidden sm:inline">
                                Vec: {src.vector_score.toFixed(2)}
                              </span>
                            )}
                            {src.keyword_score !== null && src.keyword_score !== undefined && (
                              <span className="px-1.5 py-0.5 rounded bg-cyan-950/40 border border-cyan-800/30 text-cyan-300 text-[10px] hidden sm:inline">
                                KW: {src.keyword_score.toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Step 13: Verification & Quality Assessment Card */}
              {(isEvaluating || isRevising || evaluationResult) && (
                <div className="mt-4 p-4 rounded-xl bg-slate-900/95 border border-emerald-500/30 space-y-3.5 shadow-lg">
                  {/* Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-semibold text-slate-200">Verification</span>
                      {isEvaluating ? (
                        <Badge variant="info" dot>Evaluating Output...</Badge>
                      ) : isRevising ? (
                        <Badge variant="warning" dot>AI Revision in Progress (Attempt {revisionAttempts})...</Badge>
                      ) : evaluationResult?.status === "passed" ? (
                        <Badge variant="success" dot>Verification Passed</Badge>
                      ) : evaluationResult?.status === "warning" ? (
                        <Badge variant="warning" dot>Verification Warning</Badge>
                      ) : (
                        <Badge variant="destructive" dot>Verification Failed</Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      {evaluationResult?.duration_ms !== undefined && (
                        <span className="text-slate-400">
                          Latency: <strong className="text-emerald-400">{evaluationResult.duration_ms}ms</strong>
                        </span>
                      )}
                      {evaluationResult?.recommendation && (
                        <span className="text-slate-400">
                          • Recommendation:{" "}
                          <strong className={
                            evaluationResult.recommendation === "accept"
                              ? "text-emerald-300"
                              : evaluationResult.recommendation === "revise"
                              ? "text-amber-300"
                              : "text-rose-300"
                          }>
                            {evaluationResult.recommendation}
                          </strong>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Revision Banner if recommended */}
                  {evaluationResult?.recommendation === "revise" && !isRevising && (
                    <div className="p-3 rounded-lg bg-amber-950/60 border border-amber-500/40 text-amber-200 text-xs flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                        <span>The result needs improvement based on verification findings.</span>
                      </div>
                      <Button
                        variant="primary"
                        size="xs"
                        icon={RefreshCw}
                        onClick={handleExecuteTask}
                        disabled={isRunning || isRevising}
                        className="bg-amber-600 hover:bg-amber-500 text-white font-semibold shrink-0"
                      >
                        Improve Answer
                      </Button>
                    </div>
                  )}

                  {/* AI Revision in Progress indicator */}
                  {isRevising && (
                    <div className="p-3 rounded-lg bg-indigo-950/80 border border-indigo-500/50 text-indigo-200 text-xs flex items-center gap-2.5 animate-pulse">
                      <Sparkles className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
                      <span className="font-semibold">AI revision in progress... (Attempt {revisionAttempts} of 2)</span>
                    </div>
                  )}

                  {/* Checks Grid / Observable Findings */}
                  {evaluationResult?.checks && evaluationResult.checks.length > 0 && (
                    <div className="space-y-2 pt-1">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {evaluationResult.checks.map((check, idx) => {
                          const isPassed = check.status === "passed";
                          const isWarning = check.status === "warning";

                          return (
                            <div
                              key={check.type || idx}
                              className={`p-2.5 rounded-lg border text-xs font-mono space-y-1.5 transition-all ${
                                isPassed
                                  ? "bg-emerald-950/20 border-emerald-800/40 text-emerald-300"
                                  : isWarning
                                  ? "bg-amber-950/30 border-amber-800/50 text-amber-300"
                                  : "bg-rose-950/30 border-rose-800/50 text-rose-300"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1.5 font-semibold capitalize">
                                  {isPassed ? (
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                  ) : isWarning ? (
                                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                                  ) : (
                                    <XCircle className="w-3.5 h-3.5 text-rose-400" />
                                  )}
                                  <span>{check.type}</span>
                                </div>
                                {check.confidence !== undefined && check.confidence !== null && (
                                  <span className="text-[10px] text-slate-400">
                                    {(check.confidence * 100).toFixed(0)}% conf
                                  </span>
                                )}
                              </div>

                              {/* Issues or findings list */}
                              {check.issues && check.issues.length > 0 ? (
                                <div className="space-y-1 pt-1 border-t border-slate-800/60">
                                  {check.issues.map((issue, iIdx) => {
                                    const desc = typeof issue === "string" ? issue : issue.description || issue.reason || issue.claim;
                                    const evidenceIds = issue.evidence_ids || [];
                                    return (
                                      <div key={iIdx} className="text-[11px] leading-relaxed text-slate-300">
                                        <span>• {desc}</span>
                                        {evidenceIds.length > 0 && (
                                          <div className="flex flex-wrap gap-1 mt-0.5">
                                            {evidenceIds.map((eid) => (
                                              <span key={eid} className="px-1 py-0.2 rounded bg-slate-950 text-[9px] text-indigo-300 border border-slate-800">
                                                {eid}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              ) : (
                                <div className="text-[10px] text-slate-400">
                                  {isPassed ? "✓ Verified & adheres to policy" : "No issues reported"}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {evaluationError && (
                    <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-[11px]">
                      {evaluationError}
                    </div>
                  )}
                </div>
              )}

              {/* Execution Run Telemetry Footer Bar */}
              {activeRun && (
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5 font-medium text-slate-300">
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    <span>Run Telemetry:</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 font-mono">
                    {activeRun.model_name && (
                      <span className="text-slate-300">
                        Model: <strong className="text-cyan-400">{activeRun.final_model || activeRun.model_name}</strong>
                        {activeRun.model_provider && (
                          <span className="text-slate-400 ml-1">({activeRun.model_provider})</span>
                        )}
                      </span>
                    )}
                    {activeRun.model_routing_policy && (
                      <span className="text-slate-300">
                        • Policy: <strong className="text-indigo-300">{activeRun.model_routing_policy}</strong>
                      </span>
                    )}
                    {activeRun.estimated_cost !== null && activeRun.estimated_cost !== undefined ? (
                      <span className="text-emerald-300 flex items-center gap-1">
                        <Coins className="w-3 h-3 text-emerald-400" />
                        Cost: <strong>${Number(activeRun.estimated_cost).toFixed(6)}</strong>
                      </span>
                    ) : (
                      <span className="text-slate-500 flex items-center gap-1">
                        <Coins className="w-3 h-3 text-slate-500" />
                        Cost: unconfigured
                      </span>
                    )}
                    {activeRun.fallback_attempts && activeRun.fallback_attempts.length > 0 && (
                      <span className="text-amber-400 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                        Failover: {activeRun.fallback_attempts.length} attempts
                      </span>
                    )}
                    {activeRun.step_count !== null && activeRun.step_count !== undefined && (
                      <span>
                        • Steps: <strong className="text-purple-300">{activeRun.step_count}</strong>
                      </span>
                    )}
                    {activeRun.orchestration_duration_ms !== null && activeRun.orchestration_duration_ms !== undefined && (
                      <span>
                        • Orchestration: <strong className="text-cyan-300">{activeRun.orchestration_duration_ms}ms</strong>
                      </span>
                    )}
                    {activeRun.tools_used && activeRun.tools_used.length > 0 && (
                      <span>
                        • Tools: <strong className="text-emerald-400">{activeRun.tools_used.join(", ")}</strong>
                        {activeRun.tool_latency_ms ? ` (${activeRun.tool_latency_ms}ms)` : ""}
                      </span>
                    )}
                    {activeRun.context_item_count !== null && activeRun.context_item_count !== undefined && (
                      <span>
                        • Context: <strong className="text-indigo-400">{activeRun.context_item_count} items</strong> ({activeRun.estimated_context_tokens || 0} tok)
                        {activeRun.context_truncated && (
                          <span className="text-amber-400 ml-1">(Truncated)</span>
                        )}
                      </span>
                    )}
                    {activeRun.latency_ms !== null && activeRun.latency_ms !== undefined && (
                      <span>• Latency: <strong className="text-emerald-400">{activeRun.latency_ms}ms</strong></span>
                    )}
                    {activeRun.total_tokens !== null && activeRun.total_tokens !== undefined && (
                      <span>• Tokens: <strong className="text-indigo-300">{activeRun.total_tokens}</strong> (in: {activeRun.input_tokens || 0}, out: {activeRun.output_tokens || 0})</span>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Context Inspector / Debug View (Section 12) */}
          {showInspector && (
            <Card className="border-indigo-900/60 bg-slate-900/90">
              <CardHeader className="py-3 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <Compass className="w-4 h-4 text-indigo-400" />
                  <CardTitle className="text-sm">Context Engine Inspector (Debug View)</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="xs" onClick={handleInspectContext} disabled={isLoadingInspect}>
                    Refresh Inspection
                  </Button>
                  <Button variant="ghost" size="xs" onClick={() => setShowInspector(false)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {isLoadingInspect ? (
                  <div className="py-8 text-center text-xs text-slate-400">Assembling context inspection package...</div>
                ) : inspectData ? (
                  <div className="space-y-4">
                    {/* Summary Metrics Bar */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">Total Items</span>
                        <span className="text-base font-bold text-white font-mono">{inspectData.total_items}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">Estimated Tokens</span>
                        <span className="text-base font-bold text-indigo-400 font-mono">
                          {inspectData.estimated_tokens} / {inspectData.max_context_tokens}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">Truncation Status</span>
                        <span className="text-xs font-semibold font-mono block mt-1">
                          {inspectData.truncated ? (
                            <span className="text-amber-400 flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" /> Truncated ({inspectData.dropped_items_count} dropped)
                            </span>
                          ) : (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Full Context Preserved
                            </span>
                          )}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                        <span className="text-[10px] text-slate-400 block">Sources Ingested</span>
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {inspectData.sources.map((s) => (
                            <Badge key={s} variant="outline" className="text-[9px] py-0">
                              {s}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Assembled Items List */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-300 block">
                        Included Context Items ({inspectData.items.length})
                      </span>
                      <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                        {inspectData.items.map((item, idx) => (
                          <div
                            key={item.id || idx}
                            className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs font-mono space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-indigo-400 font-semibold">#{idx + 1}</span>
                                <Badge variant="outline" className="text-[10px]">{item.source_type}</Badge>
                                <span className="font-semibold text-slate-200">{item.title}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {getPriorityBadge(item.priority)}
                                <span className="text-slate-400">{item.token_estimate} tok</span>
                              </div>
                            </div>
                            <p className="text-slate-400 text-[11px] line-clamp-2">{item.content}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Formatted Prompt Payload Preview */}
                    {inspectData.formatted_prompt_preview && (
                      <div className="space-y-1.5 pt-2 border-t border-slate-800">
                        <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                          <Code className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Assembled LLM Messages Snapshot</span>
                        </span>
                        <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-[180px]">
                          {inspectData.formatted_prompt_preview}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : null}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Run History Section */}
      <Card>
        <CardHeader className="py-3 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-400" />
            <CardTitle className="text-sm">Run History ({runs.length})</CardTitle>
          </div>
          <Button variant="ghost" size="sm" icon={RefreshCw} onClick={fetchTaskRuns} disabled={isLoadingRuns}>
            Refresh Runs
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingRuns ? (
            <div className="p-6 text-center text-xs text-slate-400">Loading historical runs...</div>
          ) : runs.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">
              No previous execution runs recorded for this task. Click &apos;Run Task with Context Engine&apos; above to create the first run.
            </div>
          ) : (
            <div className="divide-y divide-slate-850">
              {runs.map((run) => {
                const isSelected = activeRun?.id === run.id;
                return (
                  <div
                    key={run.id}
                    onClick={() => handleSelectPastRun(run)}
                    className={`p-3.5 sm:px-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-indigo-950/40 border-l-2 border-indigo-500"
                        : "hover:bg-slate-850/40"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                      <span className="font-mono text-xs text-indigo-400 font-medium">
                        {run.id.slice(0, 8)}...
                      </span>
                      {getStatusBadge(run.status)}
                      {run.planner_mode && (
                        <Badge variant="outline" className="text-[10px] text-cyan-300 border-cyan-800/40 capitalize font-mono">
                          {run.planner_mode}
                        </Badge>
                      )}
                      {run.iteration_count > 1 && (
                        <Badge variant="purple" className="text-[10px] bg-purple-950 text-purple-300 border-purple-800 font-mono">
                          {run.iteration_count} iters
                        </Badge>
                      )}
                      {run.repair_count > 0 && (
                        <Badge variant="warning" className="text-[10px] font-mono">
                          {run.repair_count} repair
                        </Badge>
                      )}
                      {run.model_name && (
                        <span className="text-xs text-slate-300 font-mono hidden md:inline">
                          {run.final_model || run.model_name}
                          {run.model_provider ? ` (${run.model_provider})` : ""}
                        </span>
                      )}
                      {run.fallback_attempts && run.fallback_attempts.length > 0 && (
                        <Badge variant="warning" className="text-[10px] font-mono">
                          failover
                        </Badge>
                      )}
                      {run.estimated_cost !== null && run.estimated_cost !== undefined ? (
                        <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-800/40 font-mono">
                          ${Number(run.estimated_cost).toFixed(6)}
                        </Badge>
                      ) : null}
                      {run.retrieval_required || run.retrieval_enabled ? (
                        <div className="hidden sm:flex items-center gap-1.5">
                          {getStrategyBadge(run.retrieval_strategy)}
                          <Badge variant="outline" className="text-[10px] text-purple-300 border-purple-800/40">
                            {run.retrieval_scope || "project"}
                          </Badge>
                        </div>
                      ) : (
                        <Badge variant="outline" className="text-[10px] text-slate-500 hidden sm:inline-flex">
                          No retrieval
                        </Badge>
                      )}
                      {run.tools_used && run.tools_used.length > 0 && (
                        <Badge variant="success" className="text-[10px] bg-emerald-950/60 text-emerald-300 border-emerald-800/40 hidden sm:inline-flex">
                          {run.tools_used.join(", ")}
                        </Badge>
                      )}
                      {(run.step_count || run.execution_steps?.length) && (
                        <Badge variant="outline" className="text-[10px] text-cyan-300 border-cyan-800/40 hidden md:inline-flex">
                          {run.step_count || run.execution_steps?.length} steps
                        </Badge>
                      )}
                      {run.evaluation_status && run.evaluation_status !== "not_run" && (
                        <Badge
                          variant={
                            run.evaluation_status === "passed"
                              ? "success"
                              : run.evaluation_status === "warning"
                              ? "warning"
                              : "destructive"
                          }
                          className="text-[10px] font-mono hidden sm:inline-flex"
                        >
                          eval: {run.evaluation_status}
                        </Badge>
                      )}
                      {run.revision_attempts > 0 && (
                        <Badge variant="warning" className="text-[10px] font-mono hidden md:inline-flex">
                          {run.revision_attempts} rev
                        </Badge>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
                      {run.orchestration_duration_ms !== null && run.orchestration_duration_ms !== undefined && (
                        <span className="text-cyan-300 flex items-center gap-1 hidden lg:inline-flex">
                          <Workflow className="w-3 h-3 text-cyan-400" />
                          {run.orchestration_duration_ms}ms orch
                        </span>
                      )}
                      {run.context_item_count !== null && run.context_item_count !== undefined && (
                        <span className="text-indigo-300 flex items-center gap-1">
                          <Layers className="w-3 h-3 text-indigo-400" />
                          {run.context_item_count} ctx ({run.estimated_context_tokens || 0} tok)
                        </span>
                      )}
                      {run.total_tokens !== null && run.total_tokens !== undefined && (
                        <span className="flex items-center gap-1 text-slate-300">
                          <Zap className="w-3 h-3 text-amber-400" />
                          {run.total_tokens} tok
                        </span>
                      )}
                      {run.latency_ms !== null && run.latency_ms !== undefined && (
                        <span className="flex items-center gap-1 text-emerald-400">
                          <Clock className="w-3 h-3" />
                          {run.latency_ms}ms
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-slate-400 text-[11px]">
                        <Calendar className="w-3 h-3" />
                        {formatDate(run.created_at)}
                      </span>
                    </div>
                  </div>
                );
              })}

            </div>
          )}
        </CardContent>
      </Card>

      {/* Add / Edit Context Modal */}
      <Modal
        isOpen={isContextModalOpen}
        onClose={() => setIsContextModalOpen(false)}
        title={editingContext ? "Edit Context Item" : "Add Task Context"}
        description="Provide background documentation, technical constraints, or data notes for the Context Engine."
      >
        <form onSubmit={handleSaveContextItem} className="space-y-4">
          {contextError && (
            <div className="p-3 rounded-lg bg-rose-950 border border-rose-800 text-rose-300 text-xs">
              {contextError}
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1">
              Context Title / Label *
            </label>
            <input
              type="text"
              value={modalTitle}
              onChange={(e) => setModalTitle(e.target.value)}
              placeholder="e.g. FastAPI JWT Authentication Notes"
              className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <label className="font-medium text-slate-300">Context Content *</label>
              <span className="font-mono text-[11px] text-indigo-400">
                ~{estimateTokensLocal(modalContent)} estimated tokens
              </span>
            </div>
            <textarea
              value={modalContent}
              onChange={(e) => setModalContent(e.target.value)}
              placeholder="Paste relevant domain documentation, rules, schema definitions, or reference material..."
              rows={6}
              className="w-full rounded-lg bg-slate-900 border border-slate-700 p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono leading-relaxed"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <label className="font-medium text-slate-300">Priority Weight (0 - 100)</label>
              <span className="font-mono text-indigo-400 font-semibold">{modalPriority}</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={modalPriority}
              onChange={(e) => setModalPriority(parseInt(e.target.value, 10))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Low (10)</span>
              <span>Medium (50)</span>
              <span>High (80)</span>
              <span>Critical (100)</span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              type="button"
              onClick={() => setIsContextModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={isSavingContext || !modalTitle.trim() || !modalContent.trim()}
            >
              {isSavingContext ? "Saving..." : editingContext ? "Update Context" : "Add Context"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

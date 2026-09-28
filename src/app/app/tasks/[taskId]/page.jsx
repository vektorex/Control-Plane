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

  // Retrieval Router Preview / Debug state (Step 8)
  const [previewDecision, setPreviewDecision] = useState(null);
  const [isPreviewingRetrieval, setIsPreviewingRetrieval] = useState(false);
  const [previewError, setPreviewError] = useState(null);

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

  useEffect(() => {
    loadModels();
    loadTaskAndContexts();
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

  // Run Task Execution
  const handleExecuteTask = async (e) => {
    e?.preventDefault();
    if (!taskId || !selectedModel) return;

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
      });
    } catch (err) {
      console.warn("Auto-save prior to run failed:", err);
    }

    setExecutionError(null);
    setOutputStream("");
    setIsRunning(true);
    setElapsedMs(0);
    setActiveRun(null);

    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 50);

    const runPayload = {
      model: selectedModel,
      temperature: Number(temperature),
      max_context_tokens: Number(contextBudget),
      retrieval_mode: retrievalMode,
      retrieval_strategy: retrievalStrategy || undefined,
      retrieval_scope: retrievalScope,
      retrieval_top_k: Number(retrievalTopK),
      retrieval_project_scope: retrievalScope === "project",
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
            model_name: selectedModel,
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
            created_at: new Date().toISOString(),
          });
        },
        onChunk: (delta) => {
          accumulated += delta;
          setOutputStream(accumulated);
        },
        onRunCompleted: (completedRun) => {
          setActiveRun(completedRun);
          setOutputStream(completedRun.output_content || accumulated);
          fetchTaskRuns();
        },
        onError: (err) => {
          clearInterval(timerRef.current);
          setIsRunning(false);
          setExecutionError(err.message || "Execution error encountered during task run.");
          fetchTaskRuns();
        },
        onComplete: () => {
          clearInterval(timerRef.current);
          setIsRunning(false);
        },
      });
    } else {
      try {
        const completedRun = await taskService.executeTask(taskId, runPayload);
        setActiveRun(completedRun);
        setOutputStream(completedRun.output_content || "");
        await fetchTaskRuns();
      } catch (err) {
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
  };

  const handleCopy = () => {
    if (!outputStream) return;
    navigator.clipboard.writeText(outputStream);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
                {/* Model Selector */}
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1.5">
                    Target LLM Model
                  </label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.provider})
                      </option>
                    ))}
                    {models.length === 0 && (
                      <option value="" disabled>
                        Loading registered models...
                      </option>
                    )}
                  </select>
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
                    Run Task with Context Engine
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
                  <span className="text-xs">Click &apos;Run Task with Context Engine&apos; to execute this task</span>
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
                        Model: <strong className="text-cyan-400">{activeRun.model_name}</strong>
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
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs text-indigo-400 font-medium">
                        {run.id.slice(0, 8)}...
                      </span>
                      {getStatusBadge(run.status)}
                      {run.model_name && (
                        <span className="text-xs text-slate-300 font-mono hidden md:inline">
                          {run.model_name}
                        </span>
                      )}
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
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
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

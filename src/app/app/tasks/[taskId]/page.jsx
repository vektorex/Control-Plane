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
import { Input, Textarea } from "@/components/ui/Input";
import { taskService } from "@/services/tasks";
import { orchestratorService } from "@/services/orchestrator";
import { runService } from "@/services/runs";
import { formatDate } from "@/lib/utils";
import {
  Play,
  Square,
  Sparkles,
  Cpu,
  Zap,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  Clock,
  ArrowLeft,
  Save,
  CheckCircle2,
  FileText,
  Layers,
  History,
  Terminal,
  Activity,
  Calendar,
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

  // Models & execution settings
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [temperature, setTemperature] = useState(0.2);
  const [enableStreaming, setEnableStreaming] = useState(true);

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

  // Load task and runs
  const loadTaskAndRuns = async () => {
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

      // Fetch runs
      await fetchTaskRuns();
    } catch (err) {
      console.error("[TaskWorkspace] Error loading task:", err);
      setExecutionError(err.message || "Failed to load task details");
    } finally {
      setIsLoadingTask(false);
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

  useEffect(() => {
    loadModels();
    loadTaskAndRuns();
  }, [taskId]);

  // Save task modifications (title, instructions, context)
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

    // Auto-save any updated instructions first
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
            onClick={loadTaskAndRuns}
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
        {/* Left Column: Task Definition & Execution Parameters */}
        <div className="lg:col-span-5 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Task Specification</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Define the explicit instructions and contextual information passed to the AI model.
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
                  placeholder="Explain exactly what the AI model must accomplish (e.g., 'Analyze the API architecture and write unit test fixtures')..."
                  rows={6}
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono leading-relaxed"
                  required
                />
              </div>

              {/* Context Text */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center justify-between">
                  <span>Context / Input Data (Optional)</span>
                  <span className="text-[10px] text-slate-400 font-normal">Supplementary text</span>
                </label>
                <textarea
                  value={contextText}
                  onChange={(e) => setContextText(e.target.value)}
                  placeholder="Paste relevant snippets, source documents, JSON payloads, or domain constraints..."
                  rows={4}
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 font-mono leading-relaxed"
                />
              </div>

              {/* Model & Parameters Controls */}
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

                {/* Temperature Slider */}
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
                  <div className="flex justify-between text-[10px] text-slate-400">
                    <span>0.0 (Deterministic)</span>
                    <span>0.2 (Focused)</span>
                    <span>1.0 (Creative)</span>
                  </div>
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
              <div className="pt-2">
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
                    Run Task
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: AI Output & Live Telemetry */}
        <div className="lg:col-span-7 space-y-4">
          <Card className="flex flex-col h-full min-h-[560px]">
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
                  <span className="text-xs">Orchestrating task with {selectedModel}...</span>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center flex-1 py-16 text-slate-500 space-y-2">
                  <Terminal className="w-8 h-8 text-slate-700" />
                  <span className="text-xs">Click &apos;Run Task&apos; to execute this task with AI</span>
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
              No previous execution runs recorded for this task. Click &apos;Run Task&apos; above to create the first run.
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
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
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
    </div>
  );
}

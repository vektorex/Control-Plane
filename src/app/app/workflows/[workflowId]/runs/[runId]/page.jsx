"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { workflowService } from "@/services/workflows";
import { useEventStream } from "@/lib/events";
import {
  Workflow,
  ArrowLeft,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  Coins,
  Cpu,
  RefreshCw,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Sliders,
  Sparkles,
  Search,
  Wrench,
  Bot,
  ShieldCheck,
  Split,
  GitFork,
  FileCheck,
  Activity,
  Loader2,
  ShieldAlert,
  ExternalLink,
  Layers,
} from "lucide-react";

const stepIcons = {
  input: Sliders,
  context: Sparkles,
  retrieve: Search,
  tool: Wrench,
  generate: Bot,
  evaluate: ShieldCheck,
  transform: Split,
  condition: GitFork,
  output: FileCheck,
};

export default function WorkflowRunDetailPage({ params }) {
  const unwrappedParams = use(params);
  const { workflowId, runId } = unwrappedParams;

  const [run, setRun] = useState(null);
  const [traceEvents, setTraceEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [activeTab, setActiveTab] = useState("steps"); // 'steps' | 'trace' | 'input'
  const [error, setError] = useState(null);

  const fetchRunData = async () => {
    try {
      setLoading(true);
      setError(null);
      const runRes = await workflowService.getWorkflowRun(runId);
      setRun(runRes);

      try {
        const traceRes = await workflowService.getWorkflowRunTrace(runId);
        setTraceEvents(traceRes?.events || []);
      } catch (tErr) {
        console.warn("[WorkflowRunDetail] Could not load trace events:", tErr);
      }
    } catch (err) {
      console.error("[WorkflowRunDetail] Failed to load run:", err);
      setError(err.message || "Failed to load workflow run data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRunData();
  }, [runId]);

  // Step 26: Real-time execution stream for workflow runs with fallback polling
  const { isConnected: isSseConnected, isPollingFallback } = useEventStream({
    workspaceId: run?.workspace_id,
    eventType: "workflow.*",
    aggregateId: runId,
    onEvent: (event) => {
      fetchRunData();
    },
    fallbackPollingInterval: 3000,
    fallbackPollingFn: run && (run.status === "running" || run.status === "queued" || run.status === "retrying") ? fetchRunData : undefined,
  });

  // Bounded auto-refresh polling (only when SSE is not connected or in fallback)
  useEffect(() => {
    if (isSseConnected) return;
    let pollCount = 0;
    const maxPolls = 60; // Bounded interval: max 3 minutes of auto-polling
    const interval = setInterval(() => {
      if (run && (run.status === "running" || run.status === "queued" || run.status === "retrying")) {
        if (pollCount++ < maxPolls) {
          fetchRunData();
        } else {
          clearInterval(interval);
        }
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [runId, run?.status, isSseConnected]);

  const toggleStep = (stepId) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepId]: !prev[stepId],
    }));
  };

  const handleCopyOutput = () => {
    if (!run?.output_data) return;
    const text =
      typeof run.output_data === "object"
        ? JSON.stringify(run.output_data, null, 2)
        : String(run.output_data);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
        <p className="text-sm">Loading execution run details...</p>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-8 text-center text-slate-300">
        <p>Workflow run not found.</p>
        <Link href={`/app/workflows/${workflowId}`}>
          <Button variant="outline" className="mt-4">
            Back to Builder
          </Button>
        </Link>
      </div>
    );
  }

  const isCompleted = run.status === "completed";
  const isFailed = run.status === "failed";
  const isWaitingApproval = run.status === "waiting_for_approval";
  const durationMs = run.duration_ms || 0;
  const executionState = run.execution_state || {};
  const stepResults = run.step_results || [];

  return (
    <div className="space-y-6 pb-16 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <Link href={`/app/workflows/${workflowId}`}>
            <button className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100">
                {run.workflow_name || "Workflow"} Run
              </h1>
              <Badge
                variant={
                  isWaitingApproval
                    ? "default"
                    : isCompleted
                    ? "success"
                    : isFailed
                    ? "destructive"
                    : "default"
                }
                className={`text-[10px] uppercase font-mono ${
                  isWaitingApproval
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse"
                    : ""
                }`}
              >
                {run.status.replace("_", " ")}
              </Badge>
              <Badge variant="outline" className="text-[10px] font-mono">
                v{run.workflow_version}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Run ID: <span className="text-slate-300">{run.id}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchRunData}
            disabled={loading}
            className="text-xs gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Link href={`/app/workflows/${workflowId}`}>
            <Button variant="primary" size="sm" className="text-xs gap-1.5">
              <Workflow className="w-3.5 h-3.5" />
              <span>Open in Builder</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Human Approval Waiting Banner */}
      {isWaitingApproval && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-amber-950/20">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-bold text-amber-300">Waiting for human approval</h4>
                <Badge className="bg-amber-500/25 text-amber-300 border-amber-500/40 text-[10px] font-mono">
                  PAUSED
                </Badge>
              </div>
              <p className="text-xs text-slate-300">
                Execution paused at step{" "}
                <span className="font-mono text-amber-300 font-semibold">
                  {executionState.pending_step_id || "approval_step"}
                </span>{" "}
                until authorization is submitted.
              </p>
              <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-0.5">
                <span>Intervention ID: <span className="font-mono text-slate-300">{executionState.intervention_id || "N/A"}</span></span>
                <span>Paused: <span className="font-mono text-slate-300">{executionState.paused_at ? new Date(executionState.paused_at).toLocaleTimeString() : "Just now"}</span></span>
              </div>
            </div>
          </div>

          {executionState.intervention_id && (
            <Link href={`/app/approvals/${executionState.intervention_id}`}>
              <Button size="sm" className="bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs gap-1.5 shrink-0 shadow-md">
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open Approval</span>
              </Button>
            </Link>
          )}
        </div>
      )}

      {/* Human Rejection Notice */}
      {isFailed && run.error_code?.startsWith("human_intervention_") && (
        <div className="p-3.5 bg-red-950/30 border border-red-500/30 rounded-xl text-red-300 text-xs flex items-center gap-2.5">
          <XCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>Workflow execution was halted because human intervention was rejected.</span>
        </div>
      )}

      {/* Approved Execution Notice */}
      {executionState.variables?.__approved_steps__ && Object.keys(executionState.variables.__approved_steps__).length > 0 && (
        <div className="p-3 bg-emerald-950/25 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>
            Human approval was granted for steps: {Object.keys(executionState.variables.__approved_steps__).join(", ")}.
          </span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Durable Background Job Integration Banner */}
      {(run.job_id || executionState?.job_id) && (
        <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-800/40 flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-200">Durable Background Job:</span>
                <span className="font-mono text-indigo-300 font-bold">{run.job_id || executionState.job_id}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Managed asynchronously by PostgreSQL durable queue with automatic retry policies and lease protection.
              </p>
            </div>
          </div>
          <Link
            href="/app/jobs"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-300 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 transition-colors shrink-0"
          >
            <span>Job Center</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Execution Time"
          value={`${(durationMs / 1000).toFixed(2)}s`}
          icon={Clock}
          trend={{ value: run.started_at ? new Date(run.started_at).toLocaleTimeString() : "N/A" }}
        />
        <StatCard
          label="Total Tokens"
          value={run.total_tokens?.toLocaleString() ?? "0"}
          icon={Cpu}
          trend={{ value: "Observed usage" }}
        />
        <StatCard
          label="Estimated Cost"
          value={`$${(run.estimated_cost_usd || 0).toFixed(5)}`}
          icon={Coins}
          trend={{ value: "Model routing" }}
        />
        <StatCard
          label="Steps Executed"
          value={`${run.steps_completed || stepResults.length} / ${run.step_count || stepResults.length}`}
          icon={Activity}
          trend={{ value: isCompleted ? "All passed" : run.status }}
        />
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("steps")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "steps"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Step Execution ({stepResults.length})
        </button>
        <button
          onClick={() => setActiveTab("output")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "output"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Final Output
        </button>
        <button
          onClick={() => setActiveTab("trace")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "trace"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Telemetry Trace ({traceEvents.length})
        </button>
        <button
          onClick={() => setActiveTab("input")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            activeTab === "input"
              ? "bg-indigo-600 text-white"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Input Parameters
        </button>
      </div>

      {/* TAB: Steps Execution Timeline */}
      {activeTab === "steps" && (
        <div className="space-y-4">
          <div className="space-y-3">
            {stepResults.map((st, index) => {
              const Icon = stepIcons[st.step_type] || Activity;
              const isStepFailed = st.status === "failed";
              const isExpanded = Boolean(expandedSteps[st.step_id]);

              return (
                <Card
                  key={st.step_id || index}
                  className="p-4 bg-slate-900/70 border-slate-800 hover:border-slate-700 transition-colors"
                >
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleStep(st.step_id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[11px] font-mono font-semibold text-slate-300">
                        {index + 1}
                      </div>

                      <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        <Icon className="w-4 h-4" />
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-slate-100">
                            {st.step_name || st.step_id}
                          </span>
                          <Badge
                            variant={isStepFailed ? "destructive" : "success"}
                            className="text-[10px] font-mono uppercase"
                          >
                            {st.status}
                          </Badge>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {st.step_type}
                          </span>
                        </div>
                        {st.output_summary && (
                          <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                            {st.output_summary}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {st.duration_ms !== undefined && (
                        <span className="text-xs text-slate-400 font-mono">
                          {st.duration_ms}ms
                        </span>
                      )}
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Step Detail */}
                  {isExpanded && (
                    <div className="pt-3 mt-3 border-t border-slate-800/80 space-y-2">
                      {st.error && (
                        <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded text-rose-400 text-xs font-mono">
                          Error: {st.error}
                        </div>
                      )}

                      <div className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                        Step Output State
                      </div>
                      <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-64">
                        {typeof st.output_data === "object"
                          ? JSON.stringify(st.output_data, null, 2)
                          : String(st.output_data || "No output")}
                      </pre>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>

          {stepResults.length === 0 && (
            <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
              <p className="text-xs text-slate-400">No step executions recorded for this run.</p>
            </Card>
          )}
        </div>
      )}

      {/* TAB: Final Output */}
      {activeTab === "output" && (
        <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-slate-100">Workflow Final Output</h3>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyOutput}
              className="text-xs gap-1.5"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Output</span>
                </>
              )}
            </Button>
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80 text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
            {typeof run.output_data === "object"
              ? JSON.stringify(run.output_data, null, 2)
              : String(run.output_data || "Workflow completed with no output.")}
          </div>
        </Card>
      )}

      {/* TAB: Trace Events */}
      {activeTab === "trace" && (
        <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-3">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Execution Observability Trace
          </div>
          <div className="space-y-2">
            {traceEvents.map((evt, idx) => (
              <div
                key={evt.id || idx}
                className="p-2.5 rounded bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <Badge variant="outline" className="text-[10px] font-mono">
                    {evt.event_type}
                  </Badge>
                  <span className="font-medium text-slate-200">{evt.event_name}</span>
                </div>
                <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
                  <span className="capitalize">{evt.status}</span>
                  {evt.duration_ms !== undefined && <span>• {evt.duration_ms}ms</span>}
                </div>
              </div>
            ))}
          </div>

          {traceEvents.length === 0 && (
            <p className="text-xs text-slate-400 text-center py-4">No trace events recorded.</p>
          )}
        </Card>
      )}

      {/* TAB: Input Parameters */}
      {activeTab === "input" && (
        <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-3">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Runtime Input Parameters
          </div>
          <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto">
            {JSON.stringify(run.input_data || {}, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}

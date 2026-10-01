"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Coins,
  Copy,
  Cpu,
  Database,
  ExternalLink,
  Eye,
  Layers,
  ListOrdered,
  ListTodo,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  Workflow,
  Wrench,
  XCircle,
  Zap,
  Brain,
  RotateCcw,
  Bug,
  Info,
  SlidersHorizontal,
  Play,
  X,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { analyticsService } from "@/services/analytics";
import { runService } from "@/services/runs";
import { replayService } from "@/services/replay";
import { formatDate } from "@/lib/utils";

export default function RunExecutionTracePage({ params: paramsProp }) {
  const router = useRouter();
  const routeParams = useParams();
  const runId = routeParams?.runId || (paramsProp ? use(paramsProp)?.runId : null);

  const [traceData, setTraceData] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [usageRecords, setUsageRecords] = useState([]);
  const [runDetail, setRunDetail] = useState(null);
  const [failureInsights, setFailureInsights] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expandedEvents, setExpandedEvents] = useState({});

  // Step 21: Debug Studio & Replay triggers
  const [activeTab, setActiveTab] = useState("trace"); // "trace" | "debug_studio"
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayActionMsg, setReplayActionMsg] = useState(null);

  const loadTraceAndTelemetry = useCallback(async () => {
    if (!runId) return;
    try {
      setIsLoading(true);
      setError(null);

      const [traceRes, telemRes, usageRes, runRes, failureRes] = await Promise.allSettled([
        analyticsService.getRunTrace(runId),
        analyticsService.getRunTelemetry(runId),
        analyticsService.getRunUsage(runId),
        runService.getRun(runId),
        replayService.getFailureInsights(runId),
      ]);

      if (traceRes.status === "fulfilled") setTraceData(traceRes.value);
      if (telemRes.status === "fulfilled") setTelemetry(telemRes.value);
      if (usageRes.status === "fulfilled") setUsageRecords(usageRes.value?.usage_records || []);
      if (runRes.status === "fulfilled") setRunDetail(runRes.value);
      if (failureRes.status === "fulfilled") setFailureInsights(failureRes.value);
    } catch (err) {
      console.error("[RunTrace] Error fetching trace details:", err);
      setError(err.message || "Failed to load execution trace.");
    } finally {
      setIsLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    loadTraceAndTelemetry();
  }, [loadTraceAndTelemetry]);

  const toggleExpand = (seq, e) => {
    if (e) e.stopPropagation();
    setExpandedEvents((prev) => ({ ...prev, [seq]: !prev[seq] }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLaunchReplay = async (mode = "dry_run") => {
    if (!runId) return;
    try {
      setReplayLoading(true);
      setReplayActionMsg(null);
      let res;
      if (mode === "inspect") {
        res = await replayService.inspectRunReplay(runId);
      } else {
        res = await replayService.dryRunReplay(runId);
      }
      router.push(`/app/replays/${res.id}`);
    } catch (err) {
      setReplayActionMsg(err.message || "Failed to start replay.");
    } finally {
      setReplayLoading(false);
    }
  };

  const getStageIcon = (eventType, stepType) => {
    if (eventType?.includes("plan")) return Workflow;
    if (eventType?.includes("retriev")) return Database;
    if (eventType?.includes("tool")) return Wrench;
    if (eventType?.includes("generat")) return Sparkles;
    if (eventType?.includes("evaluat")) return ShieldCheck;
    if (eventType?.includes("revis")) return Sparkles;
    return Activity;
  };

  const getStageBadgeColor = (eventType, status) => {
    if (status === "failed" || eventType?.includes("failed")) {
      return "bg-rose-950/60 text-rose-300 border-rose-800/60";
    }
    if (eventType?.includes("plan")) {
      return "bg-slate-900 text-slate-300 border-slate-700";
    }
    if (eventType?.includes("retriev")) {
      return "bg-purple-950/40 text-purple-300 border-purple-800/50";
    }
    if (eventType?.includes("tool")) {
      return "bg-emerald-950/40 text-emerald-300 border-emerald-800/50";
    }
    if (eventType?.includes("generat")) {
      return "bg-cyan-950/40 text-cyan-300 border-cyan-800/50";
    }
    if (eventType?.includes("evaluat")) {
      return "bg-indigo-950/40 text-indigo-300 border-indigo-800/50";
    }
    return "bg-slate-900 text-slate-300 border-slate-700";
  };

  const events = traceData?.events || [];
  const runStatus = telemetry?.final_status || runDetail?.status || "unknown";

  // Build high-level pipeline stage progression (Section 13)
  const pipelineStages = [
    {
      id: "task_analysis",
      name: "Task Analysis",
      status: runDetail?.task_type ? "completed" : "skipped",
      detail: runDetail?.task_type ? `Type: ${runDetail.task_type}` : "Standard direct mode",
    },
    {
      id: "planning",
      name: "Planning",
      status: events.some((e) => e.event_type?.includes("plan")) ? "completed" : "skipped",
      detail: telemetry?.planner_model || "Hybrid planner",
    },
    {
      id: "retrieval",
      name: "Retrieval",
      status: (telemetry?.retrieval_calls > 0 || runDetail?.retrieval_enabled) ? "completed" : "skipped",
      detail: `${telemetry?.retrieval_results || 0} chunks retrieved`,
    },
    {
      id: "tools",
      name: "Tools",
      status: (telemetry?.tool_calls > 0 || (runDetail?.tools_used?.length > 0)) ? "completed" : "skipped",
      detail: `${telemetry?.tool_calls || 0} tools executed`,
    },
    {
      id: "generation",
      name: "Generation",
      status: events.some((e) => e.event_type?.includes("generat") && e.status === "failed")
        ? "failed"
        : events.some((e) => e.event_type?.includes("generat"))
        ? "completed"
        : runStatus === "completed"
        ? "completed"
        : "skipped",
      detail: telemetry?.generation_model || runDetail?.model_name || "gpt-4o-mini",
    },
    {
      id: "evaluation",
      name: "Evaluation",
      status: telemetry?.evaluation_status ? (telemetry.evaluation_status === "failed" ? "failed" : "completed") : "skipped",
      detail: telemetry?.evaluation_status ? `Status: ${telemetry.evaluation_status}` : "Skipped",
    },
    {
      id: "revision",
      name: "Revision",
      status: telemetry?.revision_attempts > 0 ? "completed" : "skipped",
      detail: telemetry?.revision_attempts > 0 ? `${telemetry.revision_attempts} revisions` : "None needed",
    },
    {
      id: "completion",
      name: "Completion",
      status: runStatus === "completed" ? "completed" : runStatus === "failed" ? "failed" : "running",
      detail: `${telemetry?.duration_ms || runDetail?.latency_ms || 0} ms`,
    },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="xs"
              onClick={() => router.back()}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-medium text-slate-400">Observability</span>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-mono text-indigo-400">Execution Trace</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Run Telemetry &amp; Trace
            </h1>

            <Badge
              variant={
                runStatus === "completed"
                  ? "success"
                  : runStatus === "failed"
                  ? "destructive"
                  : "outline"
              }
              className="capitalize text-xs font-mono"
            >
              {runStatus}
            </Badge>

            {runId && (
              <button
                onClick={() => copyToClipboard(runId)}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-400 hover:text-slate-200 transition-colors"
                title="Copy Run ID"
              >
                <span>ID: {runId}</span>
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              </button>
            )}
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {telemetry?.task_id && (
            <Link
              href={`/app/tasks/${telemetry.task_id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700/50 text-xs font-medium text-indigo-300 transition-colors"
            >
              <ListTodo className="w-3.5 h-3.5 text-indigo-400" />
              <span>View Task</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleLaunchReplay("dry_run")}
            disabled={replayLoading}
            className="text-xs text-blue-300 border-blue-800/80 hover:bg-blue-950/60"
          >
            <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${replayLoading ? "animate-spin" : ""}`} />
            Dry-Run Replay
          </Button>

          <Button
            size="sm"
            onClick={() => setActiveTab(activeTab === "debug_studio" ? "trace" : "debug_studio")}
            className="text-xs bg-indigo-600 hover:bg-indigo-500 font-semibold"
          >
            <Bug className="w-3.5 h-3.5 mr-1.5" />
            {activeTab === "debug_studio" ? "View Raw Trace" : "Debug Execution"}
          </Button>

          <Button variant="outline" size="sm" onClick={loadTraceAndTelemetry} disabled={isLoading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {replayActionMsg && (
        <div className="p-3 rounded-lg text-xs font-mono bg-rose-950/60 border border-rose-800 text-rose-300">
          {replayActionMsg}
        </div>
      )}

      {/* Failure Diagnostics Banner (Section 34) */}
      {(failureInsights || runStatus === "failed") && (
        <Card className="bg-rose-950/40 border-rose-800/80">
          <CardHeader className="p-4 border-b border-rose-900/40">
            <CardTitle className="text-sm flex items-center gap-2 text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              Factual Failure Diagnostics
            </CardTitle>
            <CardDescription className="text-xs text-rose-200/70">
              Deterministic diagnostic analysis derived from error telemetry without subjective model ranking.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-3 text-xs font-mono">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-2.5 rounded bg-slate-950/80 border border-rose-900/40">
                <span className="text-[10px] text-slate-400 block uppercase">Failure Code</span>
                <span className="text-xs font-bold text-rose-300 mt-0.5 block">
                  {failureInsights?.failure_code || telemetry?.error_type || "UNKNOWN_ERROR"}
                </span>
              </div>
              <div className="p-2.5 rounded bg-slate-950/80 border border-rose-900/40">
                <span className="text-[10px] text-slate-400 block uppercase">Pipeline Stage</span>
                <span className="text-xs font-bold text-white mt-0.5 block">
                  {failureInsights?.stage || "Execution"}
                </span>
              </div>
              <div className="p-2.5 rounded bg-slate-950/80 border border-rose-900/40">
                <span className="text-[10px] text-slate-400 block uppercase">Retry / Fallback</span>
                <span className="text-xs text-slate-300 mt-0.5 block">
                  {failureInsights?.retry_attempts ?? 0} retries, {failureInsights?.fallback_attempts ?? 0} fallbacks
                </span>
              </div>
              <div className="p-2.5 rounded bg-slate-950/80 border border-rose-900/40">
                <span className="text-[10px] text-slate-400 block uppercase">Execution Duration</span>
                <span className="text-xs text-slate-300 mt-0.5 block">
                  {failureInsights?.duration_ms ?? telemetry?.duration_ms ?? 0} ms
                </span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 flex items-start gap-2">
              <Info className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-rose-200">Diagnostic Action: </span>
                <span className="text-rose-100">
                  {failureInsights?.suggested_action || "Review trace timeline events below or replay with another compatible model."}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* High-Level Pipeline Stages (Section 13) */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800">
          <CardTitle className="text-sm flex items-center gap-2">
            <Workflow className="w-4 h-4 text-indigo-400" />
            Execution Pipeline Progression
          </CardTitle>
          <CardDescription className="text-xs">
            High-level lifecycle stages executed by the AI Work Layer for this run.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {pipelineStages.map((st, i) => {
              const isCompleted = st.status === "completed";
              const isFailed = st.status === "failed";
              const isSkipped = st.status === "skipped";

              return (
                <div
                  key={st.id}
                  className={`p-2.5 rounded-lg border text-center space-y-1 transition-all ${
                    isFailed
                      ? "bg-rose-950/50 border-rose-800/80 text-rose-300"
                      : isCompleted
                      ? "bg-emerald-950/30 border-emerald-800/60 text-emerald-300"
                      : "bg-slate-950 border-slate-800 text-slate-500"
                  }`}
                >
                  <div className="flex items-center justify-center gap-1">
                    {isFailed ? (
                      <XCircle className="w-3.5 h-3.5 text-rose-400" />
                    ) : isCompleted ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                    )}
                    <span className="text-[11px] font-bold tracking-tight truncate block">
                      {st.name}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 block truncate">
                    {st.detail}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Trace Timeline Card */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              Execution Trace Event Timeline ({events.length})
            </CardTitle>
            <CardDescription className="text-xs">
              Click any event below to inspect full sanitized configuration, token telemetry, and execution details.
            </CardDescription>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {events.length} events
          </span>
        </CardHeader>

        <CardContent className="p-4 space-y-3">
          {events.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 font-mono">
              No trace events recorded for this run.
            </div>
          ) : (
            <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-4">
              {events.map((evt, idx) => {
                const Icon = getStageIcon(evt.event_type, evt.step_type);
                const isExpanded = !!expandedEvents[evt.sequence_number];
                const isFailed = evt.status === "failed" || evt.event_type?.includes("failed");

                return (
                  <div key={evt.id || idx} className="relative group">
                    {/* Dot indicator on timeline */}
                    <div
                      className={`absolute -left-[31px] top-2 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all ${
                        isFailed
                          ? "bg-rose-950 border-rose-500 text-rose-400"
                          : "bg-slate-950 border-indigo-500 text-indigo-400 group-hover:border-indigo-400"
                      }`}
                    >
                      <div
                        className={`w-1.5 h-1.5 rounded-full ${
                          isFailed ? "bg-rose-400" : "bg-indigo-400"
                        }`}
                      />
                    </div>

                    {/* Event Card */}
                    <div
                      onClick={() => setSelectedEvent(evt)}
                      className={`p-3.5 rounded-lg border text-xs transition-all cursor-pointer hover:border-indigo-500/80 ${getStageBadgeColor(
                        evt.event_type,
                        evt.status
                      )}`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-[10px] text-slate-400 font-semibold px-1.5 py-0.5 rounded bg-slate-950/80 border border-slate-800">
                            #{evt.sequence_number}
                          </span>

                          <div className="flex items-center gap-1.5 font-bold tracking-tight text-slate-100 font-mono">
                            <Icon className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                            <span>{evt.event_type}</span>
                          </div>

                          {evt.step_type && (
                            <Badge variant="outline" className="text-[10px] capitalize">
                              {evt.step_type}
                            </Badge>
                          )}

                          {evt.model && (
                            <span className="font-mono text-[11px] text-cyan-300">
                              {evt.model}
                              {evt.provider ? ` (${evt.provider})` : ""}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 font-mono text-[11px]">
                          {evt.duration_ms !== null && evt.duration_ms !== undefined && (
                            <span className="text-emerald-400 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {evt.duration_ms} ms
                            </span>
                          )}

                          <Badge
                            variant={
                              evt.status === "completed"
                                ? "success"
                                : evt.status === "failed"
                                ? "destructive"
                                : "outline"
                            }
                            className="text-[10px] capitalize"
                          >
                            {evt.status}
                          </Badge>

                          <span className="text-slate-400 text-[10px] font-mono hover:text-white underline">
                            Inspect Details
                          </span>
                        </div>
                      </div>

                      {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                        <div className="mt-2 text-[11px] text-slate-300 font-mono">
                          {Object.entries(evt.metadata)
                            .slice(0, 3)
                            .map(([k, v]) => (
                              <span key={k} className="mr-3 text-slate-400">
                                <span className="text-slate-500">{k}:</span> {typeof v === "object" ? JSON.stringify(v) : String(v)}
                              </span>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Event Detail Drawer / Modal (Section 14) */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-slate-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                  #{selectedEvent.sequence_number}
                </span>
                <h3 className="text-base font-bold text-white font-mono">
                  {selectedEvent.event_type}
                </h3>
              </div>
              <button onClick={() => setSelectedEvent(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Overview */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Overview
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Status</span>
                  <span className="text-white font-semibold capitalize">{selectedEvent.status}</span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Duration</span>
                  <span className="text-emerald-400">{selectedEvent.duration_ms ?? "—"} ms</span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Step Type</span>
                  <span className="text-cyan-300">{selectedEvent.step_type || "None"}</span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Timestamp</span>
                  <span className="text-slate-300 text-[10px]">{formatDate(selectedEvent.created_at)}</span>
                </div>
              </div>
            </div>

            {/* Configuration */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Configuration
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Model &amp; Provider</span>
                  <span className="text-white font-bold">{selectedEvent.model || "Default"} ({selectedEvent.provider || "openai"})</span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Operation</span>
                  <span className="text-slate-200">{selectedEvent.step_type || selectedEvent.event_type}</span>
                </div>
              </div>
            </div>

            {/* Metadata / Result Summary */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Sanitized Execution Metadata
              </span>
              <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                {JSON.stringify(selectedEvent.metadata || {}, null, 2)}
              </pre>
            </div>

            {selectedEvent.error_code && (
              <div className="p-3 rounded bg-rose-950/60 border border-rose-800 text-xs font-mono text-rose-300 space-y-1">
                <span className="font-semibold block">Error Code: {selectedEvent.error_code}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <Button size="sm" variant="outline" onClick={() => setSelectedEvent(null)} className="text-xs">
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

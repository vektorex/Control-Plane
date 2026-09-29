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
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { analyticsService } from "@/services/analytics";
import { runService } from "@/services/runs";
import { formatDate } from "@/lib/utils";

export default function RunExecutionTracePage({ params: paramsProp }) {
  const router = useRouter();
  const routeParams = useParams();
  const runId = routeParams?.runId || (paramsProp ? use(paramsProp)?.runId : null);

  const [traceData, setTraceData] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [usageRecords, setUsageRecords] = useState([]);
  const [runDetail, setRunDetail] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expandedEvents, setExpandedEvents] = useState({});

  const loadTraceAndTelemetry = useCallback(async () => {
    if (!runId) return;
    try {
      setIsLoading(true);
      setError(null);

      const [traceRes, telemRes, usageRes, runRes] = await Promise.allSettled([
        analyticsService.getRunTrace(runId),
        analyticsService.getRunTelemetry(runId),
        analyticsService.getRunUsage(runId),
        runService.getRun(runId),
      ]);

      if (traceRes.status === "fulfilled") setTraceData(traceRes.value);
      if (telemRes.status === "fulfilled") setTelemetry(telemRes.value);
      if (usageRes.status === "fulfilled") setUsageRecords(usageRes.value?.usage_records || []);
      if (runRes.status === "fulfilled") setRunDetail(runRes.value);
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

  const toggleExpand = (seq) => {
    setExpandedEvents((prev) => ({ ...prev, [seq]: !prev[seq] }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
              Run Telemetry & Trace
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

        <div className="flex items-center gap-2">
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

          <Button variant="outline" size="sm" onClick={loadTraceAndTelemetry} disabled={isLoading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-7 h-7 text-indigo-400 animate-spin" />
          <span className="text-xs text-slate-400 font-mono">Loading telemetry trace stream...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Telemetry Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Total Duration
              </span>
              <span className="text-base font-bold text-emerald-400 font-mono mt-1 block">
                {telemetry?.duration_ms !== null && telemetry?.duration_ms !== undefined
                  ? `${telemetry.duration_ms} ms`
                  : runDetail?.latency_ms
                  ? `${runDetail.latency_ms} ms`
                  : "—"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Total Tokens
              </span>
              <span className="text-base font-bold text-indigo-400 font-mono mt-1 block">
                {telemetry?.total_tokens?.toLocaleString() || runDetail?.total_tokens?.toLocaleString() || 0}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                in: {telemetry?.input_tokens || 0} · out: {telemetry?.output_tokens || 0}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Estimated Cost
              </span>
              <span className="text-base font-bold text-emerald-400 font-mono mt-1 block">
                {telemetry?.estimated_cost !== null && telemetry?.estimated_cost !== undefined
                  ? `$${Number(telemetry.estimated_cost).toFixed(6)}`
                  : runDetail?.estimated_cost !== null && runDetail?.estimated_cost !== undefined
                  ? `$${Number(runDetail.estimated_cost).toFixed(6)}`
                  : "Unconfigured"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Model Routed
              </span>
              <span className="text-xs font-bold text-cyan-300 font-mono mt-1 block truncate">
                {telemetry?.generation_model || runDetail?.final_model || runDetail?.model_name || "—"}
              </span>
              <span className="text-[10px] text-slate-400 capitalize">
                {telemetry?.provider || runDetail?.model_provider || "—"}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Tools & Retrieval
              </span>
              <span className="text-xs font-semibold text-slate-200 font-mono mt-1 block">
                {telemetry?.tool_calls || 0} tools · {telemetry?.retrieval_results || 0} chunks
              </span>
              {telemetry?.tools_used && telemetry.tools_used.length > 0 && (
                <span className="text-[10px] text-emerald-400 block truncate">
                  {telemetry.tools_used.join(", ")}
                </span>
              )}
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Verification
              </span>
              <span className="text-xs font-semibold font-mono mt-1 block">
                {telemetry?.evaluation_status ? (
                  <Badge
                    variant={
                      telemetry.evaluation_status === "passed"
                        ? "success"
                        : telemetry.evaluation_status === "warning"
                        ? "warning"
                        : "destructive"
                    }
                    className="text-[10px]"
                  >
                    {telemetry.evaluation_status}
                  </Badge>
                ) : (
                  <span className="text-slate-500">Not Evaluated</span>
                )}
              </span>
              {telemetry?.revision_attempts > 0 && (
                <span className="text-[10px] text-amber-400 font-mono block">
                  {telemetry.revision_attempts} revisions
                </span>
              )}
            </div>
          </div>

          {/* Safe Error Details Card (if failed) */}
          {telemetry?.error_message_safe && (
            <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-300 space-y-1 text-xs">
              <div className="flex items-center gap-2 font-semibold">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>Execution Error ({telemetry.error_type || "UNKNOWN_ERROR"})</span>
              </div>
              <p className="font-mono text-[11px] text-rose-200/90 pl-6">
                {telemetry.error_message_safe}
              </p>
            </div>
          )}

          {/* Execution Trace Timeline */}
          <Card className="bg-slate-900/60 border-slate-800">
            <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  Execution Trace Event Timeline
                </CardTitle>
                <CardDescription className="text-xs">
                  Step-by-step telemetry events across planning, retrieval, tools, generation, and verification.
                </CardDescription>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {events.length} trace events
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
                          className={`p-3.5 rounded-lg border text-xs transition-all ${getStageBadgeColor(
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

                              {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                                <button
                                  onClick={() => toggleExpand(evt.sequence_number)}
                                  className="text-slate-400 hover:text-slate-200 flex items-center gap-0.5"
                                  title="Inspect Sanitized Metadata"
                                >
                                  {isExpanded ? (
                                    <ChevronDown className="w-4 h-4" />
                                  ) : (
                                    <ChevronRight className="w-4 h-4" />
                                  )}
                                </button>
                              )}
                            </div>
                          </div>

                          {/* Error Code display */}
                          {evt.error_code && (
                            <div className="mt-2 p-2 rounded bg-rose-950/90 border border-rose-800 text-rose-300 font-mono text-[11px]">
                              Error Code: {evt.error_code}
                            </div>
                          )}

                          {/* Expanded Sanitized Metadata Viewer */}
                          {isExpanded && evt.metadata && (
                            <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1">
                              <div className="flex items-center justify-between text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                                <span>Sanitized Telemetry Metadata</span>
                                <span className="text-slate-500 font-mono">No raw secrets or CoT</span>
                              </div>
                              <pre className="p-2.5 rounded bg-slate-950/90 border border-slate-800 text-[11px] text-indigo-200/90 font-mono overflow-x-auto leading-relaxed max-h-60 overflow-y-auto">
                                {JSON.stringify(evt.metadata, null, 2)}
                              </pre>
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

          {/* Usage Records Granular Table */}
          {usageRecords.length > 0 && (
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader className="p-4 border-b border-slate-800">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Coins className="w-4 h-4 text-emerald-400" />
                  Granular Usage Records Breakdown
                </CardTitle>
                <CardDescription className="text-xs">
                  Normalized token accounting and price calculation per pipeline operation.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950/80 text-slate-400 font-mono border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-4">Operation</th>
                        <th className="py-2.5 px-4">Model</th>
                        <th className="py-2.5 px-4">Provider</th>
                        <th className="py-2.5 px-4">Input Tokens</th>
                        <th className="py-2.5 px-4">Output Tokens</th>
                        <th className="py-2.5 px-4">Total Tokens</th>
                        <th className="py-2.5 px-4">Estimated Cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {usageRecords.map((u) => (
                        <tr key={u.id} className="hover:bg-slate-850/40">
                          <td className="py-3 px-4 font-mono font-semibold text-slate-200 capitalize">
                            {u.operation}
                          </td>
                          <td className="py-3 px-4 font-mono text-cyan-300">{u.model}</td>
                          <td className="py-3 px-4 capitalize font-medium text-slate-300">
                            {u.provider}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-400">
                            {u.input_tokens?.toLocaleString() || 0}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-400">
                            {u.output_tokens?.toLocaleString() || 0}
                          </td>
                          <td className="py-3 px-4 font-mono text-indigo-300 font-bold">
                            {u.total_tokens?.toLocaleString() || 0}
                          </td>
                          <td className="py-3 px-4 font-mono text-emerald-400">
                            {u.estimated_cost !== null && u.estimated_cost !== undefined
                              ? `$${Number(u.estimated_cost).toFixed(6)}`
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

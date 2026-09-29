"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  Calendar,
  Clock,
  Coins,
  Cpu,
  Database,
  ExternalLink,
  Filter,
  Layers,
  ListTodo,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  Trash2,
  TrendingUp,
  Workflow,
  Wrench,
  XCircle,
  Zap,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { analyticsService } from "@/services/analytics";
import { projectService } from "@/services/projects";
import { orchestratorService } from "@/services/orchestrator";
import { useWorkspace } from "@/lib/workspaceContext";
import { formatDate } from "@/lib/utils";

export default function AnalyticsDashboardPage() {
  const { activeWorkspace } = useWorkspace();

  // Filter state
  const [period, setPeriod] = useState("30d");
  const [selectedProject, setSelectedProject] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");

  // Projects and models for filters
  const [projects, setProjects] = useState([]);
  const [registeredModels, setRegisteredModels] = useState([]);

  // Data state
  const [overview, setOverview] = useState(null);
  const [usage, setUsage] = useState(null);
  const [modelsData, setModelsData] = useState([]);
  const [providersData, setProvidersData] = useState([]);
  const [latencyData, setLatencyData] = useState(null);
  const [evaluationsData, setEvaluationsData] = useState(null);
  const [recentTelemetry, setRecentTelemetry] = useState([]);

  // Loading and error states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Retention cleanup modal state
  const [isCleanupModalOpen, setIsCleanupModalOpen] = useState(false);
  const [retentionDays, setRetentionDays] = useState(30);
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleanupResult, setCleanupResult] = useState(null);

  // Active sub-tab in dashboard
  const [activeTab, setActiveTab] = useState("overview"); // overview | usage | models | evaluations | recent

  // Load project list for active workspace
  const loadProjects = useCallback(async () => {
    if (!activeWorkspace?.id) return;
    try {
      const res = await projectService.listProjects({ workspace_id: activeWorkspace.id });
      setProjects(res?.projects || res || []);
    } catch (err) {
      console.warn("[Analytics] Failed to load projects:", err);
    }
  }, [activeWorkspace?.id]);

  // Load model registry
  const loadModels = useCallback(async () => {
    try {
      const res = await orchestratorService.getModels();
      setRegisteredModels(res?.models || []);
    } catch (err) {
      console.warn("[Analytics] Failed to load registered models:", err);
    }
  }, []);

  // Calculate start date based on period filter
  const getPeriodDateRange = useCallback(() => {
    const now = new Date();
    let startDate = null;
    if (period === "24h") {
      startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    } else if (period === "7d") {
      startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    } else if (period === "30d") {
      startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    } else if (period === "90d") {
      startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
    }
    return {
      start_date: startDate ? startDate.toISOString() : undefined,
      end_date: now.toISOString(),
    };
  }, [period]);

  // Main fetch function
  const fetchAnalyticsData = useCallback(async () => {
    if (!activeWorkspace?.id) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const dateRange = getPeriodDateRange();
      const params = {
        workspace_id: activeWorkspace.id,
        ...(selectedProject ? { project_id: selectedProject } : {}),
        ...(selectedModel ? { model: selectedModel } : {}),
        ...(selectedProvider ? { provider: selectedProvider } : {}),
        ...(selectedStatus ? { status: selectedStatus } : {}),
        ...(dateRange.start_date ? { start_date: dateRange.start_date } : {}),
        ...(dateRange.end_date ? { end_date: dateRange.end_date } : {}),
      };

      const [ovRes, usRes, mdRes, prRes, latRes, evRes] = await Promise.allSettled([
        analyticsService.getOverview(params),
        analyticsService.getUsage({ ...params, group_by: "day" }),
        analyticsService.getModels(params),
        analyticsService.getProviders(params),
        analyticsService.getLatency(params),
        analyticsService.getEvaluations(params),
      ]);

      if (ovRes.status === "fulfilled") setOverview(ovRes.value);
      if (usRes.status === "fulfilled") setUsage(usRes.value);
      if (mdRes.status === "fulfilled") setModelsData(mdRes.value?.models || []);
      if (prRes.status === "fulfilled") setProvidersData(prRes.value?.providers || []);
      if (latRes.status === "fulfilled") setLatencyData(latRes.value);
      if (evRes.status === "fulfilled") setEvaluationsData(evRes.value);
    } catch (err) {
      console.error("[Analytics] Error fetching dashboard data:", err);
      setError(err.message || "Failed to load telemetry analytics.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [
    activeWorkspace?.id,
    getPeriodDateRange,
    selectedProject,
    selectedModel,
    selectedProvider,
    selectedStatus,
  ]);

  useEffect(() => {
    loadProjects();
    loadModels();
  }, [loadProjects, loadModels]);

  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchAnalyticsData();
  };

  const handleCleanupRetention = async () => {
    if (!activeWorkspace?.id) return;
    try {
      setIsCleaning(true);
      setCleanupResult(null);
      const res = await analyticsService.cleanupObservability({
        workspace_id: activeWorkspace.id,
        retention_days: retentionDays,
      });
      setCleanupResult(res);
      fetchAnalyticsData();
    } catch (err) {
      setCleanupResult({ error: err.message || "Cleanup failed" });
    } finally {
      setIsCleaning(false);
    }
  };

  const hasData = overview && overview.runs && overview.runs.total > 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header & Controls Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Observability & Cost Intelligence
                <Badge variant="outline" className="text-[10px] text-cyan-400 border-cyan-800/40">
                  Telemetry Active
                </Badge>
              </h1>
              <p className="text-xs text-slate-400">
                Factual execution telemetry, token usage, cost accounting, and multi-stage latency analysis.
              </p>
            </div>
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsCleanupModalOpen(true)}
            className="text-xs text-slate-300 border-slate-700"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
            Retention Cleanup
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
            className="text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardContent className="p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-1.5 text-slate-400 font-medium mr-1">
              <Filter className="w-3.5 h-3.5 text-indigo-400" />
              <span>Filters:</span>
            </div>

            {/* Time Period Selector */}
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="all">All Time</option>
            </select>

            {/* Project Filter */}
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            >
              <option value="">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>

            {/* Model Filter */}
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            >
              <option value="">All Models</option>
              {registeredModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name || m.id} ({m.provider})
                </option>
              ))}
            </select>

            {/* Provider Filter */}
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            >
              <option value="">All Providers</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="groq">Groq</option>
              <option value="mock">Mock / Dev</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed Only</option>
              <option value="failed">Failed Only</option>
            </select>
          </div>

          {(selectedProject || selectedModel || selectedProvider || selectedStatus || period !== "30d") && (
            <Button
              variant="ghost"
              size="xs"
              onClick={() => {
                setPeriod("30d");
                setSelectedProject("");
                setSelectedModel("");
                setSelectedProvider("");
                setSelectedStatus("");
              }}
              className="text-[11px] text-slate-400 hover:text-white"
            >
              Reset Filters
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 text-xs font-medium">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-2.5 px-3 border-b-2 font-medium transition-colors ${
            activeTab === "overview"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Executive Overview
        </button>
        <button
          onClick={() => setActiveTab("usage")}
          className={`pb-2.5 px-3 border-b-2 font-medium transition-colors ${
            activeTab === "usage"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Usage & Cost Trends
        </button>
        <button
          onClick={() => setActiveTab("models")}
          className={`pb-2.5 px-3 border-b-2 font-medium transition-colors ${
            activeTab === "models"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Model Telemetry
        </button>
        <button
          onClick={() => setActiveTab("evaluations")}
          className={`pb-2.5 px-3 border-b-2 font-medium transition-colors ${
            activeTab === "evaluations"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Evaluation Quality
        </button>
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
          <span className="text-xs text-slate-400 font-mono">Aggregating telemetry and cost records...</span>
        </div>
      ) : !hasData ? (
        <EmptyState
          icon={BarChart3}
          title="No Telemetry Recorded for this Period"
          description="Execute tasks through the orchestrator to populate production telemetry, token consumption logs, latency benchmarks, and cost calculations."
          actionLabel="Go to Tasks Workspace"
          onAction={() => (window.location.href = "/app/tasks")}
        />
      ) : (
        <div className="space-y-6">
          {/* TAB 1: EXECUTIVE OVERVIEW */}
          {activeTab === "overview" && (
            <>
              {/* 6 Core Overview Stat Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <StatCard
                  title="Total Run Executions"
                  value={overview.runs?.total?.toLocaleString() || "0"}
                  description={`${overview.runs?.successful || 0} successful · ${overview.runs?.failed || 0} failed`}
                  icon={Activity}
                />

                <StatCard
                  title="Success Rate"
                  value={
                    overview.runs?.success_rate !== null && overview.runs?.success_rate !== undefined
                      ? `${Number(overview.runs.success_rate).toFixed(1)}%`
                      : "N/A"
                  }
                  change={
                    overview.runs?.success_rate >= 90
                      ? "Healthy"
                      : overview.runs?.success_rate >= 75
                      ? "Degraded"
                      : "Critical"
                  }
                  changeType={
                    overview.runs?.success_rate >= 90
                      ? "positive"
                      : overview.runs?.success_rate >= 75
                      ? "neutral"
                      : "negative"
                  }
                  icon={TrendingUp}
                />

                <StatCard
                  title="Total Token Consumption"
                  value={overview.tokens?.total?.toLocaleString() || "0"}
                  description={`In: ${overview.tokens?.input?.toLocaleString() || 0} · Out: ${
                    overview.tokens?.output?.toLocaleString() || 0
                  }`}
                  icon={Zap}
                />

                <StatCard
                  title="Estimated LLM Cost"
                  value={
                    overview.cost?.estimated !== null && overview.cost?.estimated !== undefined
                      ? `$${Number(overview.cost.estimated).toFixed(4)}`
                      : "Unconfigured"
                  }
                  description={
                    overview.cost?.estimated !== null
                      ? "From model catalog pricing"
                      : "No pricing metadata configured"
                  }
                  icon={Coins}
                />

                <StatCard
                  title="Average End-to-End Latency"
                  value={
                    overview.latency?.average_ms !== null && overview.latency?.average_ms !== undefined
                      ? `${overview.latency.average_ms} ms`
                      : "N/A"
                  }
                  description={`p50: ${overview.latency?.p50_ms || 0} ms · p95: ${
                    overview.latency?.p95_ms || 0
                  } ms`}
                  icon={Clock}
                />

                <StatCard
                  title="Evaluation Pass Rate"
                  value={
                    overview.evaluation?.pass_rate !== null && overview.evaluation?.pass_rate !== undefined
                      ? `${Number(overview.evaluation.pass_rate).toFixed(1)}%`
                      : "N/A"
                  }
                  description={`${overview.evaluation?.passed || 0} passed · ${
                    overview.evaluation?.warning || 0
                  } warnings · ${overview.evaluation?.failed || 0} failed`}
                  icon={ShieldCheck}
                />
              </div>

              {/* Latency by Stage Breakdown */}
              {latencyData?.stages && (
                <Card className="bg-slate-900/60 border-slate-800">
                  <CardHeader className="p-4 border-b border-slate-800">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Workflow className="w-4 h-4 text-cyan-400" />
                      Stage Latency Profile & Pipeline Breakdown
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Average latency distribution across planning, retrieval, tool execution, generation, and evaluation.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400 block font-semibold">
                          1. Planning
                        </span>
                        <span className="text-base font-bold text-slate-200 font-mono mt-1 block">
                          {latencyData.stages.planning_avg_ms || 0} ms
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400 block font-semibold">
                          2. Retrieval
                        </span>
                        <span className="text-base font-bold text-purple-300 font-mono mt-1 block">
                          {latencyData.stages.retrieval_avg_ms || 0} ms
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400 block font-semibold">
                          3. Tools Execution
                        </span>
                        <span className="text-base font-bold text-emerald-300 font-mono mt-1 block">
                          {latencyData.stages.tool_avg_ms || 0} ms
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400 block font-semibold">
                          4. Generation
                        </span>
                        <span className="text-base font-bold text-cyan-300 font-mono mt-1 block">
                          {latencyData.stages.generation_avg_ms || 0} ms
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <span className="text-[10px] uppercase tracking-wider text-slate-400 block font-semibold">
                          5. Verification
                        </span>
                        <span className="text-base font-bold text-indigo-300 font-mono mt-1 block">
                          {latencyData.stages.evaluation_avg_ms || 0} ms
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Provider Market Share Table */}
              {providersData.length > 0 && (
                <Card className="bg-slate-900/60 border-slate-800">
                  <CardHeader className="p-4 border-b border-slate-800">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-indigo-400" />
                      LLM Provider Distribution & Share
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-950/80 text-slate-400 font-mono border-b border-slate-800">
                          <tr>
                            <th className="py-2.5 px-4">Provider</th>
                            <th className="py-2.5 px-4">Runs</th>
                            <th className="py-2.5 px-4">Share</th>
                            <th className="py-2.5 px-4">Total Tokens</th>
                            <th className="py-2.5 px-4">Estimated Cost</th>
                            <th className="py-2.5 px-4">Avg Latency</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {providersData.map((p) => (
                            <tr key={p.provider} className="hover:bg-slate-850/40">
                              <td className="py-3 px-4 font-semibold text-slate-200 capitalize flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-indigo-400" />
                                {p.provider}
                              </td>
                              <td className="py-3 px-4 font-mono text-slate-300">{p.runs}</td>
                              <td className="py-3 px-4 font-mono text-indigo-400">
                                {overview.runs?.total
                                  ? `${((p.runs / overview.runs.total) * 100).toFixed(1)}%`
                                  : "0%"}
                              </td>
                              <td className="py-3 px-4 font-mono text-slate-300">
                                {p.tokens?.total?.toLocaleString() || 0}
                              </td>
                              <td className="py-3 px-4 font-mono text-emerald-400">
                                {p.estimated_cost !== null && p.estimated_cost !== undefined
                                  ? `$${Number(p.estimated_cost).toFixed(4)}`
                                  : "—"}
                              </td>
                              <td className="py-3 px-4 font-mono text-cyan-400">
                                {p.average_latency_ms ? `${p.average_latency_ms} ms` : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {/* TAB 2: USAGE & COST TRENDS */}
          {activeTab === "usage" && (
            <div className="space-y-6">
              <Card className="bg-slate-900/60 border-slate-800">
                <CardHeader className="p-4 border-b border-slate-800">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-indigo-400" />
                    Daily Usage Activity & Token Consumption
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Time-series log of runs dispatched and token volume.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-4">
                  {usage?.points && usage.points.length > 0 ? (
                    <div className="space-y-3">
                      <div className="space-y-2">
                        {usage.points.map((pt) => {
                          const maxTokens = Math.max(...usage.points.map((p) => p.tokens?.total || 1), 1);
                          const pct = Math.min(100, Math.max(8, ((pt.tokens?.total || 0) / maxTokens) * 100));

                          return (
                            <div
                              key={pt.timestamp}
                              className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2"
                            >
                              <div className="flex items-center justify-between text-xs font-mono">
                                <span className="font-semibold text-slate-200">
                                  {formatDate(pt.timestamp)}
                                </span>
                                <div className="flex items-center gap-3">
                                  <span className="text-slate-400">{pt.runs} runs</span>
                                  <span className="text-indigo-300 font-bold">
                                    {pt.tokens?.total?.toLocaleString() || 0} tokens
                                  </span>
                                  {pt.estimated_cost !== null && pt.estimated_cost !== undefined && (
                                    <span className="text-emerald-400">
                                      ${Number(pt.estimated_cost).toFixed(4)}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Visual token bar */}
                              <div className="w-full h-2 rounded bg-slate-900 overflow-hidden flex">
                                <div
                                  className="h-full bg-indigo-500 rounded transition-all"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="py-8 text-center text-xs text-slate-500">
                      No daily usage points found in this period.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* TAB 3: MODEL TELEMETRY */}
          {activeTab === "models" && (
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader className="p-4 border-b border-slate-800">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  Model Operational Performance & Economics
                </CardTitle>
                <CardDescription className="text-xs">
                  Factual operational data per model. Models are not subjectively ranked.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950/80 text-slate-400 font-mono border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-4">Model</th>
                        <th className="py-2.5 px-4">Provider</th>
                        <th className="py-2.5 px-4">Runs</th>
                        <th className="py-2.5 px-4">Tokens (In / Out)</th>
                        <th className="py-2.5 px-4">Avg Latency</th>
                        <th className="py-2.5 px-4">Estimated Cost</th>
                        <th className="py-2.5 px-4">Failures</th>
                        <th className="py-2.5 px-4">Capabilities</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {modelsData.map((m) => {
                        const reg = registeredModels.find((rm) => rm.id === m.model);
                        const caps = reg?.capabilities || [];

                        return (
                          <tr key={m.model} className="hover:bg-slate-850/40">
                            <td className="py-3 px-4 font-mono font-semibold text-slate-200">
                              {m.model}
                            </td>
                            <td className="py-3 px-4 capitalize">
                              <Badge variant="outline" className="text-[10px] text-slate-300">
                                {m.provider}
                              </Badge>
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-300">{m.runs}</td>
                            <td className="py-3 px-4 font-mono text-slate-400">
                              <span className="text-indigo-300 font-medium">
                                {m.tokens?.total?.toLocaleString() || 0}
                              </span>
                              <span className="text-[10px] block text-slate-500">
                                ({m.tokens?.input?.toLocaleString() || 0} /{" "}
                                {m.tokens?.output?.toLocaleString() || 0})
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-cyan-300">
                              {m.average_latency_ms ? `${m.average_latency_ms} ms` : "—"}
                            </td>
                            <td className="py-3 px-4 font-mono text-emerald-400">
                              {m.estimated_cost !== null && m.estimated_cost !== undefined
                                ? `$${Number(m.estimated_cost).toFixed(4)}`
                                : "—"}
                            </td>
                            <td className="py-3 px-4 font-mono">
                              {m.failures > 0 ? (
                                <span className="text-rose-400 font-semibold">{m.failures}</span>
                              ) : (
                                <span className="text-slate-500">0</span>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex flex-wrap gap-1">
                                {caps.map((c) => (
                                  <span
                                    key={c}
                                    className="px-1.5 py-0.2 rounded bg-slate-950 text-[9px] text-slate-400 border border-slate-800 font-mono"
                                  >
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* TAB 4: EVALUATION QUALITY */}
          {activeTab === "evaluations" && (
            <div className="space-y-6">
              {evaluationsData ? (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-xs text-slate-400 block">Total Evaluated Runs</span>
                      <span className="text-2xl font-bold text-white font-mono mt-1 block">
                        {evaluationsData.total_evaluations}
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
                      <span className="text-xs text-emerald-400 block">Passed</span>
                      <span className="text-2xl font-bold text-emerald-300 font-mono mt-1 block">
                        {evaluationsData.passed}
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40">
                      <span className="text-xs text-amber-400 block">Warnings</span>
                      <span className="text-2xl font-bold text-amber-300 font-mono mt-1 block">
                        {evaluationsData.warning}
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40">
                      <span className="text-xs text-rose-400 block">Failed</span>
                      <span className="text-2xl font-bold text-rose-300 font-mono mt-1 block">
                        {evaluationsData.failed}
                      </span>
                    </div>
                  </div>

                  {/* Policy and Verification Insights */}
                  <Card className="bg-slate-900/60 border-slate-800">
                    <CardHeader className="p-4 border-b border-slate-800">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        Verification Policy Compliance Summary
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 space-y-3 text-xs">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                        <span className="text-slate-300">Total Autonomous Revision Attempts</span>
                        <span className="font-mono font-bold text-indigo-400">
                          {evaluationsData.revision_count || 0} attempts
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                        <span className="text-slate-300">Evaluation Pass Rate</span>
                        <span className="font-mono font-bold text-emerald-400">
                          {evaluationsData.pass_rate !== null && evaluationsData.pass_rate !== undefined
                            ? `${Number(evaluationsData.pass_rate).toFixed(1)}%`
                            : "N/A"}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">
                  No evaluation records available.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Retention Cleanup Modal */}
      <Modal
        isOpen={isCleanupModalOpen}
        onClose={() => {
          setIsCleanupModalOpen(false);
          setCleanupResult(null);
        }}
        title="Telemetry Retention & Cleanup"
        description="Permanently purge execution trace events and raw telemetry older than the specified retention window. Tasks, Runs, Documents, and Evaluation history will never be deleted."
      >
        <div className="space-y-4 text-xs">
          {cleanupResult && (
            <div
              className={`p-3 rounded-lg border ${
                cleanupResult.error
                  ? "bg-rose-950 border-rose-800 text-rose-300"
                  : "bg-emerald-950 border-emerald-800 text-emerald-300"
              }`}
            >
              {cleanupResult.error ? (
                cleanupResult.error
              ) : (
                <div>
                  <p className="font-semibold">Cleanup Executed Successfully:</p>
                  <p className="mt-1 font-mono text-[11px]">
                    Purged {cleanupResult.deleted_trace_events || 0} trace events,{" "}
                    {cleanupResult.deleted_usage_records || 0} usage records, and{" "}
                    {cleanupResult.deleted_telemetry_records || 0} telemetry rows.
                  </p>
                </div>
              )}
            </div>
          )}

          <div>
            <label className="font-medium text-slate-300 block mb-1">
              Retention Days (Older than)
            </label>
            <input
              type="number"
              min="1"
              max="365"
              value={retentionDays}
              onChange={(e) => setRetentionDays(parseInt(e.target.value, 10) || 30)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Default system retention is 30 days (configured via OBSERVABILITY_RETENTION_DAYS).
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsCleanupModalOpen(false);
                setCleanupResult(null);
              }}
            >
              Close
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCleanupRetention}
              disabled={isCleaning}
            >
              {isCleaning ? "Cleaning..." : "Purge Stale Telemetry"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

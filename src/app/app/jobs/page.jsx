"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Layers,
  Play,
  RotateCcw,
  XCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Copy,
  Check,
  ChevronRight,
  Workflow,
  Zap,
  FileText,
  FlaskConical,
  Plug,
  Server,
  Activity,
  Terminal,
  Calendar,
  ShieldCheck,
  HelpCircle,
} from "lucide-react";
import { jobService } from "@/services/jobs";
import { useAuth } from "@/lib/authContext";
import { useEventStream } from "@/lib/events";

const STATUS_CONFIG = {
  running: {
    label: "Running",
    badgeClass: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    dotClass: "bg-cyan-400 animate-pulse",
    icon: Activity,
  },
  queued: {
    label: "Queued",
    badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    dotClass: "bg-amber-400",
    icon: Clock,
  },
  retrying: {
    label: "Retrying",
    badgeClass: "bg-purple-500/10 text-purple-400 border-purple-500/30",
    dotClass: "bg-purple-400 animate-pulse",
    icon: RotateCcw,
  },
  completed: {
    label: "Completed",
    badgeClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    dotClass: "bg-emerald-400",
    icon: CheckCircle2,
  },
  failed: {
    label: "Failed",
    badgeClass: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    dotClass: "bg-rose-400",
    icon: AlertTriangle,
  },
  cancelled: {
    label: "Cancelled",
    badgeClass: "bg-slate-500/10 text-slate-400 border-slate-500/30",
    dotClass: "bg-slate-400",
    icon: XCircle,
  },
};

const JOB_TYPE_CONFIG = {
  workflow_run: { label: "Workflow Run", icon: Workflow, color: "text-indigo-400" },
  trigger_run: { label: "Trigger Run", icon: Zap, color: "text-amber-400" },
  document_processing: { label: "Document Ingestion", icon: FileText, color: "text-emerald-400" },
  evaluation_experiment: { label: "Evaluation Experiment", icon: FlaskConical, color: "text-cyan-400" },
  replay_run: { label: "Replay Run", icon: RotateCcw, color: "text-blue-400" },
  connector_operation: { label: "Connector Op", icon: Plug, color: "text-violet-400" },
};

export default function JobsPage() {
  const { user } = useAuth();
  const workspaceId = user?.default_workspace_id;

  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Inspect Modal & Action state
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobEvents, setJobEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  // Enqueue test modal
  const [showEnqueueModal, setShowEnqueueModal] = useState(false);
  const [enqueueType, setEnqueueType] = useState("document_processing");
  const [enqueuePriority, setEnqueuePriority] = useState("normal");

  const loadData = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const [jobsRes, statsRes] = await Promise.all([
        jobService.listJobs(workspaceId, {
          status: statusFilter,
          jobType: typeFilter,
          limit: 50,
        }),
        jobService.getJobStats(workspaceId),
      ]);
      setJobs(jobsRes?.jobs || []);
      setTotal(jobsRes?.total || 0);
      setStats(statsRes || null);
    } catch (err) {
      console.error("[Jobs] Failed to load jobs:", err);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, statusFilter, typeFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Step 26: Real-time SSE Execution Stream for jobs with automatic polling fallback
  const { isConnected: isSseConnected, isPollingFallback } = useEventStream({
    workspaceId,
    eventType: "job.*",
    onEvent: (event) => {
      loadData();
      if (selectedJob && event.aggregate?.id === selectedJob.id) {
        handleInspectJob({ ...selectedJob, status: event.data?.status || selectedJob.status });
      }
    },
    fallbackPollingInterval: 5000,
    fallbackPollingFn: autoRefresh ? loadData : undefined,
  });

  // Bounded auto-refresh polling (only active when autoRefresh is enabled AND SSE is in fallback/not connected)
  useEffect(() => {
    if (!autoRefresh || isSseConnected) return;
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, isSseConnected, loadData]);

  // Load details & events for selected job
  const handleInspectJob = async (job) => {
    setSelectedJob(job);
    setLoadingEvents(true);
    try {
      const [freshJob, eventsRes] = await Promise.all([
        jobService.getJob(job.id, workspaceId),
        jobService.getJobEvents(job.id, workspaceId),
      ]);
      setSelectedJob(freshJob);
      setJobEvents(eventsRes?.events || []);
    } catch (err) {
      console.error("Failed to load job events:", err);
    } finally {
      setLoadingEvents(false);
    }
  };

  const handleCancelJob = async (jobId) => {
    if (!confirm("Are you sure you want to cancel this job?")) return;
    setActionLoading(true);
    try {
      await jobService.cancelJob(jobId, workspaceId, "User requested cancellation from Job Center.");
      await loadData();
      if (selectedJob && selectedJob.id === jobId) {
        handleInspectJob({ ...selectedJob, status: "cancelled" });
      }
    } catch (err) {
      alert("Failed to cancel job: " + (err.message || err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetryJob = async (jobId) => {
    setActionLoading(true);
    try {
      await jobService.retryJob(jobId, workspaceId);
      await loadData();
      if (selectedJob && selectedJob.id === jobId) {
        handleInspectJob({ ...selectedJob, status: "queued" });
      }
    } catch (err) {
      alert("Failed to retry job: " + (err.message || err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleEnqueueSample = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await jobService.createJob(workspaceId, {
        job_type: enqueueType,
        priority: enqueuePriority,
        payload: {
          sample: true,
          description: `Test execution for ${enqueueType}`,
          timestamp: new Date().toISOString(),
        },
      });
      setShowEnqueueModal(false);
      await loadData();
    } catch (err) {
      alert("Failed to enqueue job: " + (err.message || err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredJobs = jobs.filter((job) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      job.id.toLowerCase().includes(q) ||
      (job.idempotency_key && job.idempotency_key.toLowerCase().includes(q)) ||
      job.job_type.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Durable Job Center
                <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  Step 24
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Durable PostgreSQL queue executing asynchronous AI workloads with atomic leases and crash recovery.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Link
            href="/app/settings/jobs"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors"
          >
            <Server className="w-3.5 h-3.5 text-slate-400" />
            Operations Health
          </Link>

          <div
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-800"
            title={isSseConnected ? "Live execution stream active" : isPollingFallback ? "Polling fallback active" : "Connecting..."}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isSseConnected ? "bg-emerald-400 animate-pulse" : isPollingFallback ? "bg-amber-400" : "bg-slate-500"
              }`}
            />
            <span className="text-slate-300 text-[11px]">
              {isSseConnected ? "LIVE SSE" : isPollingFallback ? "POLLING FALLBACK" : "CONNECTING"}
            </span>
          </div>

          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              autoRefresh
                ? "bg-indigo-600/15 text-indigo-300 border-indigo-500/30"
                : "bg-slate-900 text-slate-400 border-slate-800"
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${autoRefresh ? "bg-indigo-400 animate-pulse" : "bg-slate-500"}`} />
            Auto-refresh (5s)
          </button>

          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
            Refresh
          </button>

          <button
            onClick={() => setShowEnqueueModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-sm shadow-indigo-900/50 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Enqueue Job
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Jobs</span>
            <Layers className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <div className="text-xl font-bold font-mono text-white mt-1.5">{total}</div>
        </div>

        <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-800/30">
          <div className="flex items-center justify-between text-xs text-cyan-400">
            <span>Running</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          </div>
          <div className="text-xl font-bold font-mono text-cyan-300 mt-1.5">
            {stats?.running_count ?? 0}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/30">
          <div className="flex items-center justify-between text-xs text-amber-400">
            <span>Queued</span>
            <Clock className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold font-mono text-amber-300 mt-1.5">
            {stats?.queued_count ?? 0}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-800/30">
          <div className="flex items-center justify-between text-xs text-purple-400">
            <span>Retrying</span>
            <RotateCcw className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-xl font-bold font-mono text-purple-300 mt-1.5">
            {stats?.retrying_count ?? 0}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-800/30">
          <div className="flex items-center justify-between text-xs text-emerald-400">
            <span>Completed</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold font-mono text-emerald-300 mt-1.5">
            {stats?.completed_count ?? 0}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-800/30">
          <div className="flex items-center justify-between text-xs text-rose-400">
            <span>Failed</span>
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-xl font-bold font-mono text-rose-300 mt-1.5">
            {stats?.failed_count ?? 0}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
        {/* Status Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {["all", "running", "queued", "retrying", "completed", "failed", "cancelled"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize whitespace-nowrap transition-colors ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Search & Type filter */}
        <div className="flex items-center gap-2">
          <div className="relative min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search ID / Idempotency key..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1 rounded-lg text-xs bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2.5 py-1 rounded-lg text-xs bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Types</option>
            {Object.keys(JOB_TYPE_CONFIG).map((k) => (
              <option key={k} value={k}>
                {JOB_TYPE_CONFIG[k].label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-sm">
        {loading && jobs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400 mb-2" />
            Loading durable jobs...
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <Layers className="w-8 h-8 mx-auto text-slate-600 mb-2" />
            No background jobs matching the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Job Type & ID</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Progress</th>
                  <th className="px-4 py-3">Attempts</th>
                  <th className="px-4 py-3">Worker Node</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredJobs.map((job) => {
                  const statusConf = STATUS_CONFIG[job.status] || STATUS_CONFIG.queued;
                  const typeConf = JOB_TYPE_CONFIG[job.job_type] || {
                    label: job.job_type,
                    icon: Layers,
                    color: "text-slate-400",
                  };
                  const TypeIcon = typeConf.icon;
                  const progressPct = job.progress?.percentage ?? 0;

                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-slate-900/40 transition-colors group cursor-pointer"
                      onClick={() => handleInspectJob(job)}
                    >
                      {/* Status */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border ${statusConf.badgeClass}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${statusConf.dotClass}`} />
                          {statusConf.label}
                        </span>
                      </td>

                      {/* Type & ID */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <TypeIcon className={`w-4 h-4 shrink-0 ${typeConf.color}`} />
                          <div>
                            <div className="font-medium text-slate-200">{typeConf.label}</div>
                            <div className="font-mono text-[10px] text-slate-500 flex items-center gap-1">
                              <span>{job.id.slice(0, 8)}...</span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCopy(job.id, job.id);
                                }}
                                className="text-slate-500 hover:text-slate-300"
                              >
                                {copiedId === job.id ? (
                                  <Check className="w-2.5 h-2.5 text-emerald-400" />
                                ) : (
                                  <Copy className="w-2.5 h-2.5" />
                                )}
                              </button>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Priority */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${
                            job.priority === "high"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : job.priority === "low"
                              ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                              : "bg-slate-800 text-slate-300 border border-slate-700"
                          }`}
                        >
                          {job.priority}
                        </span>
                      </td>

                      {/* Progress */}
                      <td className="px-4 py-3 min-w-[140px]">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-slate-400">
                            <span>{job.progress?.current_step || (job.status === "completed" ? "Done" : "Pending")}</span>
                            <span className="font-mono">{progressPct}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all duration-300 rounded-full ${
                                job.status === "completed"
                                  ? "bg-emerald-500"
                                  : job.status === "failed"
                                  ? "bg-rose-500"
                                  : "bg-indigo-500"
                              }`}
                              style={{ width: `${progressPct}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Attempts */}
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-[11px] text-slate-400">
                        {job.attempts} / {job.max_attempts}
                      </td>

                      {/* Worker Node */}
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-[11px] text-slate-400">
                        {job.lease_owner ? (
                          <span className="text-cyan-400 truncate max-w-[120px] inline-block">
                            {job.lease_owner}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>

                      {/* Created */}
                      <td className="px-4 py-3 whitespace-nowrap text-slate-400 text-[11px]">
                        {job.created_at ? new Date(job.created_at).toLocaleTimeString() : "—"}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          {(job.status === "failed" || job.status === "cancelled") && (
                            <button
                              onClick={() => handleRetryJob(job.id)}
                              disabled={actionLoading}
                              title="Retry Job"
                              className="p-1 rounded text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition-colors"
                            >
                              <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                          )}

                          {(job.status === "queued" || job.status === "running") && (
                            <button
                              onClick={() => handleCancelJob(job.id)}
                              disabled={actionLoading}
                              title="Cancel Job"
                              className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                            >
                              <XCircle className="w-3.5 h-3.5" />
                            </button>
                          )}

                          <button
                            onClick={() => handleInspectJob(job)}
                            title="Inspect Details"
                            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect Slide-Over / Modal */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-2xl h-full bg-slate-950 border-l border-slate-800 p-6 overflow-y-auto space-y-6 shadow-2xl">
            {/* Drawer Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium border ${
                      STATUS_CONFIG[selectedJob.status]?.badgeClass
                    }`}
                  >
                    {STATUS_CONFIG[selectedJob.status]?.label}
                  </span>
                  <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {selectedJob.priority} priority
                  </span>
                  <span className="text-xs text-slate-400">{selectedJob.job_type}</span>
                </div>
                <h2 className="text-sm font-mono font-bold text-white mt-2 flex items-center gap-2">
                  {selectedJob.id}
                  <button
                    onClick={() => handleCopy(selectedJob.id, "drawer_id")}
                    className="text-slate-500 hover:text-slate-300"
                  >
                    {copiedId === "drawer_id" ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </h2>
              </div>

              <button
                onClick={() => setSelectedJob(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Action Bar */}
            <div className="flex items-center gap-2">
              {(selectedJob.status === "failed" || selectedJob.status === "cancelled") && (
                <button
                  onClick={() => handleRetryJob(selectedJob.id)}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Retry Job
                </button>
              )}

              {(selectedJob.status === "queued" || selectedJob.status === "running") && (
                <button
                  onClick={() => handleCancelJob(selectedJob.id)}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-300 bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  Cancel Job
                </button>
              )}
            </div>

            {/* Progress Section */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300">Execution Progress</span>
                <span className="font-mono text-indigo-400 font-bold">
                  {selectedJob.progress?.percentage ?? 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                  style={{ width: `${selectedJob.progress?.percentage ?? 0}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span>Step: {selectedJob.progress?.current_step || "—"}</span>
                <span>
                  {selectedJob.progress?.completed_steps ?? 0} of {selectedJob.progress?.total_steps ?? 0} steps
                </span>
              </div>
              {selectedJob.progress?.message && (
                <p className="text-[11px] text-slate-400 italic pt-1 border-t border-slate-800/80">
                  {selectedJob.progress.message}
                </p>
              )}
            </div>

            {/* Execution Metadata */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 space-y-1">
                <div className="text-slate-500 text-[10px]">Worker Node</div>
                <div className="font-mono text-cyan-400 truncate">
                  {selectedJob.lease_owner || "None (Unclaimed)"}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 space-y-1">
                <div className="text-slate-500 text-[10px]">Attempts</div>
                <div className="font-mono text-slate-200">
                  {selectedJob.attempts} of {selectedJob.max_attempts}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 space-y-1">
                <div className="text-slate-500 text-[10px]">Queue Latency</div>
                <div className="font-mono text-slate-200">
                  {selectedJob.queue_latency_ms ? `${selectedJob.queue_latency_ms} ms` : "—"}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 space-y-1">
                <div className="text-slate-500 text-[10px]">Execution Duration</div>
                <div className="font-mono text-slate-200">
                  {selectedJob.duration_ms ? `${selectedJob.duration_ms} ms` : "—"}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 space-y-1 col-span-2">
                <div className="text-slate-500 text-[10px]">Idempotency Key</div>
                <div className="font-mono text-slate-300 truncate">
                  {selectedJob.idempotency_key || "None"}
                </div>
              </div>

              {selectedJob.parent_job_id && (
                <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 space-y-1 col-span-2">
                  <div className="text-slate-500 text-[10px]">Parent Job Dependency</div>
                  <div className="font-mono text-indigo-400 truncate">{selectedJob.parent_job_id}</div>
                </div>
              )}
            </div>

            {/* Error Message Alert */}
            {selectedJob.error_message && (
              <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-1">
                <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Failure Error ({selectedJob.error_code || "JOB_FAILED"})</span>
                </div>
                <p className="text-xs text-rose-300 font-mono mt-1 whitespace-pre-wrap">
                  {selectedJob.error_message}
                </p>
              </div>
            )}

            {/* Audit Event Timeline */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Audit Event Timeline
              </h3>
              {loadingEvents ? (
                <div className="p-4 text-center text-xs text-slate-500">
                  <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-1 text-indigo-400" />
                  Loading timeline...
                </div>
              ) : jobEvents.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-500">No events recorded.</div>
              ) : (
                <div className="relative pl-6 space-y-4 border-l border-slate-800">
                  {jobEvents.map((evt, idx) => (
                    <div key={evt.id || idx} className="relative">
                      <div className="absolute -left-[31px] top-0.5 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-4 ring-slate-950" />
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-semibold text-indigo-300">{evt.event_type}</span>
                        <span className="text-slate-500">
                          {new Date(evt.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      {evt.message && <p className="text-xs text-slate-400 mt-0.5">{evt.message}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Payload & Result Inspection */}
            <div className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="font-semibold uppercase tracking-wider text-[10px]">Payload (Untrusted JSON)</span>
                  <span className="text-[10px] text-slate-500">Sanitized (No Secrets)</span>
                </div>
                <pre className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                  {JSON.stringify(selectedJob.payload || {}, null, 2)}
                </pre>
              </div>

              {selectedJob.result && (
                <div className="space-y-1.5">
                  <div className="text-xs font-semibold uppercase tracking-wider text-[10px] text-slate-400">
                    Execution Result
                  </div>
                  <pre className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-48">
                    {JSON.stringify(selectedJob.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Enqueue Sample Job Modal */}
      {showEnqueueModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
          <div className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Play className="w-4 h-4 text-indigo-400" />
                Enqueue Background Job
              </h2>
              <button
                onClick={() => setShowEnqueueModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEnqueueSample} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Job Type</label>
                <select
                  value={enqueueType}
                  onChange={(e) => setEnqueueType(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {Object.keys(JOB_TYPE_CONFIG).map((k) => (
                    <option key={k} value={k}>
                      {JOB_TYPE_CONFIG[k].label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Priority</label>
                <select
                  value={enqueuePriority}
                  onChange={(e) => setEnqueuePriority(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="high">High (Priority 1)</option>
                  <option value="normal">Normal (Priority 2)</option>
                  <option value="low">Low (Priority 3)</option>
                </select>
              </div>

              <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-800/30 text-[11px] text-indigo-300">
                This job will be atomically persisted into the PostgreSQL queue table and picked up by active workers via transactional leases.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEnqueueModal(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-sm"
                >
                  {actionLoading ? "Enqueueing..." : "Enqueue Job"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

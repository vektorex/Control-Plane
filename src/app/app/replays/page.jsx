"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  RotateCcw,
  Search,
  Filter,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Layers,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Workflow,
  Copy,
  Check,
  ExternalLink,
  SlidersHorizontal,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { replayService } from "@/services/replay";
import { formatDate } from "@/lib/utils";

export default function ReplaysPage() {
  const router = useRouter();
  const [replays, setReplays] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [modeFilter, setModeFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const loadReplays = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const params = {
        page,
        limit: 20,
      };
      if (statusFilter !== "all") params.status = statusFilter;
      if (modeFilter !== "all") params.mode = modeFilter;

      const res = await replayService.listReplays(params);
      setReplays(res.replays || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error("[ReplaysPage] Failed to fetch replays:", err);
      setError(err.message || "Failed to load execution replays.");
    } finally {
      setIsLoading(false);
    }
  }, [page, statusFilter, modeFilter]);

  useEffect(() => {
    loadReplays();
  }, [loadReplays]);

  const copyId = (id, e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return <Badge variant="success" className="text-xs">Completed</Badge>;
      case "running":
        return <Badge variant="warning" className="text-xs animate-pulse">Running</Badge>;
      case "failed":
        return <Badge variant="destructive" className="text-xs">Failed</Badge>;
      case "cancelled":
        return <Badge variant="outline" className="text-xs text-slate-400">Cancelled</Badge>;
      default:
        return <Badge variant="outline" className="text-xs capitalize">{status}</Badge>;
    }
  };

  const getModeBadge = (mode, isDryRun) => {
    const modeConfig = {
      inspect: { label: "Inspect", color: "bg-purple-950/60 text-purple-300 border-purple-800" },
      dry_run: { label: "Dry Run", color: "bg-blue-950/60 text-blue-300 border-blue-800" },
      replay: { label: "Replay", color: "bg-cyan-950/60 text-cyan-300 border-cyan-800" },
      compare: { label: "Compare", color: "bg-amber-950/60 text-amber-300 border-amber-800" },
    };
    const cfg = modeConfig[mode] || { label: mode, color: "bg-slate-900 text-slate-300 border-slate-700" };

    return (
      <div className="flex items-center gap-1.5">
        <span className={`px-2 py-0.5 rounded text-[11px] font-mono border font-medium ${cfg.color}`}>
          {cfg.label}
        </span>
        {isDryRun && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800" title="Side effects simulated safely">
            SAFE
          </span>
        )}
      </div>
    );
  };

  const filteredReplays = replays.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.id.toLowerCase().includes(q) ||
      r.original_run_id?.toLowerCase().includes(q) ||
      r.replay_mode?.toLowerCase().includes(q) ||
      r.status?.toLowerCase().includes(q)
    );
  });

  const inspectCount = replays.filter((r) => r.replay_mode === "inspect").length;
  const dryRunCount = replays.filter((r) => r.replay_mode === "dry_run").length;
  const replayCount = replays.filter((r) => r.replay_mode === "replay").length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-indigo-950 border border-indigo-700/60 flex items-center justify-center text-indigo-400 shadow-sm shadow-indigo-950">
              <RotateCcw className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Execution Replay & Debugging Studio
              </h1>
              <p className="text-xs text-slate-400">
                Safely inspect, dry-run, reproduce, and factually compare AI execution runs with strict side-effect isolation.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadReplays} disabled={isLoading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Safety Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-start sm:items-center gap-3 text-xs text-slate-300">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5 sm:mt-0" />
        <div className="flex-1">
          <span className="font-semibold text-white">Side-Effect Isolation Policy:</span> All replays default to safe dry-run mode. External write actions (e.g. GitHub issues, database mutations) are simulated unless fresh approval is granted. Original runs are immutable.
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Total Replays
          </span>
          <span className="text-2xl font-bold font-mono text-white mt-1 block">
            {total}
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider block">
            Dry-Run Simulations
          </span>
          <span className="text-2xl font-bold font-mono text-blue-300 mt-1 block">
            {dryRunCount}
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider block">
            Snapshot Inspections
          </span>
          <span className="text-2xl font-bold font-mono text-purple-300 mt-1 block">
            {inspectCount}
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider block">
            Live Re-executions
          </span>
          <span className="text-2xl font-bold font-mono text-cyan-300 mt-1 block">
            {replayCount}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Replay ID or Run ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Mode Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Mode:</span>
            <select
              value={modeFilter}
              onChange={(e) => setModeFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Modes</option>
              <option value="inspect">Inspect</option>
              <option value="dry_run">Dry Run</option>
              <option value="replay">Replay</option>
              <option value="compare">Compare</option>
            </select>
          </div>
        </div>
      </div>

      {/* Replays List */}
      <Card className="bg-slate-900/60 border-slate-800 overflow-hidden">
        <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Recorded Replays ({filteredReplays.length})
            </CardTitle>
            <CardDescription className="text-xs">
              Deterministic replay simulations and comparisons tied to historical execution runs.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <div className="py-16 text-center text-xs text-slate-500 font-mono">
              <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-slate-400" />
              Loading replay history...
            </div>
          ) : error ? (
            <div className="py-12 text-center text-xs text-rose-400 font-mono">
              {error}
            </div>
          ) : filteredReplays.length === 0 ? (
            <div className="py-16 text-center space-y-3">
              <RotateCcw className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-sm font-medium text-slate-300">No replay executions recorded yet</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Navigate to any task execution run in Observability and click &quot;Debug Execution&quot; or &quot;Dry-Run Replay&quot; to inspect and reproduce it safely.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/app/tasks")}
                className="mt-2 text-xs"
              >
                Browse Tasks
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {filteredReplays.map((replay) => {
                const meta = replay.metadata || {};
                const isModified = !!meta.modified_replay;
                const durationMs = meta.duration_ms;

                return (
                  <div
                    key={replay.id}
                    onClick={() => router.push(`/app/replays/${replay.id}`)}
                    className="p-4 hover:bg-slate-850/50 transition-colors cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        {getModeBadge(replay.replay_mode, replay.dry_run)}
                        {getStatusBadge(replay.status)}
                        {isModified && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950/60 text-amber-300 border border-amber-800">
                            Modified Replay
                          </span>
                        )}
                        <span className="text-xs font-mono text-slate-500">
                          v{replay.snapshot_version}
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                        <span className="font-mono text-slate-300 flex items-center gap-1">
                          Replay:
                          <button
                            onClick={(e) => copyId(replay.id, e)}
                            className="text-indigo-400 hover:text-indigo-300 underline font-mono flex items-center gap-1"
                          >
                            {replay.id.slice(0, 8)}...
                            {copiedId === replay.id ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3 text-slate-500" />
                            )}
                          </button>
                        </span>

                        <span className="text-slate-600">•</span>

                        <span className="flex items-center gap-1">
                          Original Run:
                          <Link
                            href={`/app/runs/${replay.original_run_id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-slate-300 hover:text-white font-mono flex items-center gap-1"
                          >
                            {replay.original_run_id.slice(0, 8)}...
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        </span>

                        {replay.original_workflow_run_id && (
                          <>
                            <span className="text-slate-600">•</span>
                            <span className="flex items-center gap-1 text-purple-300">
                              <Workflow className="w-3 h-3" />
                              Workflow
                            </span>
                          </>
                        )}
                      </div>

                      {replay.replay_output && (
                        <p className="text-xs text-slate-400 line-clamp-1 font-mono">
                          {replay.replay_output}
                        </p>
                      )}
                    </div>

                    <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-1 shrink-0 text-xs font-mono text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>{formatDate(replay.created_at)}</span>
                      </div>

                      {durationMs !== undefined && durationMs !== null && (
                        <span className="text-emerald-400 text-[11px]">
                          {durationMs} ms
                        </span>
                      )}

                      <div className="flex items-center gap-2 mt-1">
                        <Button
                          variant="ghost"
                          size="xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/app/replays/${replay.id}/compare`);
                          }}
                          className="text-indigo-400 hover:text-indigo-300 text-[11px] h-6 px-2"
                        >
                          Compare Diff
                        </Button>
                        <Button
                          variant="outline"
                          size="xs"
                          className="h-6 px-2 text-[11px]"
                        >
                          Inspect <ArrowRight className="w-3 h-3 ml-1" />
                        </Button>
                      </div>
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

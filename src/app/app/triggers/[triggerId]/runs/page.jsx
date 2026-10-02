"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RotateCcw,
  ExternalLink,
  Loader2,
  Sliders,
  Filter,
  Eye,
  X,
  Code2,
  Calendar,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { triggerService } from "@/services/triggers";
import { replayService } from "@/services/replay";

export default function TriggerRunsHistoryPage({ params }) {
  const unwrappedParams = use(params);
  const { triggerId } = unwrappedParams;

  const [trigger, setTrigger] = useState(null);
  const [runs, setRuns] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Inspector modal
  const [inspectedRun, setInspectedRun] = useState(null);
  const [replayingId, setReplayingId] = useState(null);
  const [banner, setBanner] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [trig, runList] = await Promise.all([
        triggerService.getTrigger(triggerId),
        triggerService.listTriggerRuns(triggerId, null, { limit: 50 }),
      ]);
      setTrigger(trig);
      setRuns(runList?.runs || []);
      setTotal(runList?.total || 0);
    } catch (err) {
      console.error("[TriggerRuns] Load error:", err);
      setError(err.message || "Failed to load trigger execution runs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [triggerId]);

  const handleReplayEvent = async (run) => {
    try {
      setReplayingId(run.id);
      setBanner({ type: "info", text: `Replaying event ${run.event_id || run.id} in dry-run mode...` });

      // If associated with a workflow run, dispatch to replay studio
      if (run.workflow_run_id) {
        const replay = await replayService.createReplay({
          workflow_run_id: run.workflow_run_id,
          mode: "dry_run",
          title: `Trigger Replay: ${run.event_id || run.id}`,
        });
        setBanner({
          type: "success",
          text: `Replay created in Studio! Replay ID: ${replay.id}. (External write side-effects blocked).`,
        });
      } else {
        // Test mode evaluation
        const testRes = await triggerService.testTrigger(triggerId, {
          sample_payload: run.input_snapshot || {},
        });
        setBanner({
          type: "success",
          text: `Replay evaluated: Filters ${testRes.filter_matched ? "PASSED" : "FAILED"}. Mapped inputs generated safely.`,
        });
      }
    } catch (err) {
      console.error("[TriggerReplay] Error:", err);
      setBanner({ type: "error", text: `Replay failed: ${err.message}` });
    } finally {
      setReplayingId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30">Completed</Badge>;
      case "running":
        return <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/30">Running</Badge>;
      case "queued":
        return <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/30">Queued</Badge>;
      case "skipped":
        return <Badge className="bg-slate-800 text-slate-400 border-slate-700">Skipped (Filtered/Debounced)</Badge>;
      case "failed":
        return <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/30">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href={trigger?.workflow_id ? `/app/workflows/${trigger.workflow_id}/triggers` : `/app/workflows`}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Workflow Triggers</span>
            </Link>
          </div>
          <div className="mt-1 flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-white">
              {trigger?.name || "Trigger"} &mdash; Execution History
            </h1>
            <Badge variant="outline" className="text-xs">
              {total} Total Run{total === 1 ? "" : "s"}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Immutable trace of all event receptions, filter verdicts, idempotency checks, and dispatched workflow runs.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="text-xs gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Banner */}
      {banner && (
        <div
          className={`mb-4 flex items-center justify-between rounded-lg p-3 text-xs border ${
            banner.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : banner.type === "error"
              ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
              : "bg-blue-500/10 border-blue-500/30 text-blue-300"
          }`}
        >
          <span>{banner.text}</span>
          <button onClick={() => setBanner(null)} className="text-slate-400 hover:text-slate-200">
            &times;
          </button>
        </div>
      )}

      {error && (
        <div className="mb-4 flex items-center justify-between rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-slate-200">
            &times;
          </button>
        </div>
      )}

      {/* Table */}
      {loading && runs.length === 0 ? (
        <div className="flex items-center justify-center p-16">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
        </div>
      ) : runs.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center border-slate-800 bg-slate-900/40">
          <Clock className="h-10 w-10 text-slate-600 mb-2.5" />
          <h3 className="text-sm font-semibold text-slate-200">No Executions Recorded</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm">
            This trigger has not received any events or schedules yet. Trigger it manually or wait for scheduled execution.
          </p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-950/80 uppercase text-[10px] text-slate-400 tracking-wider">
              <tr>
                <th className="px-4 py-3">Event / Delivery ID</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Workflow Run</th>
                <th className="px-4 py-3">Received At</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Retries</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <span className="font-mono text-indigo-300">
                      {r.event_id || r.id.slice(0, 12)}
                    </span>
                    {r.idempotency_key && (
                      <span className="block text-[10px] text-slate-500 font-mono">
                        key: {r.idempotency_key.slice(0, 16)}...
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(r.status)}</td>
                  <td className="px-4 py-3">
                    {r.workflow_run_id ? (
                      <Link
                        href={`/app/workflows/${trigger.workflow_id}/runs/${r.workflow_run_id}`}
                        className="flex items-center gap-1 font-mono text-indigo-400 hover:text-indigo-300"
                      >
                        <span>{r.workflow_run_id.slice(0, 8)}...</span>
                        <ExternalLink className="h-3 w-3" />
                      </Link>
                    ) : (
                      <span className="text-slate-500">None (Suppressed)</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-slate-300 font-mono">
                    {r.duration_ms ? `${r.duration_ms}ms` : "-"}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {r.retry_count > 0 ? (
                      <Badge variant="outline" className="text-[10px] text-amber-400 border-amber-500/30">
                        {r.retry_count}
                      </Badge>
                    ) : (
                      <span className="text-slate-500">0</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setInspectedRun(r)}
                        className="h-7 px-2 text-[11px] text-slate-300 hover:text-white"
                        title="Inspect snapshot"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" />
                        Inspect
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReplayEvent(r)}
                        disabled={replayingId === r.id}
                        className="h-7 px-2 text-[11px] text-indigo-400 hover:text-indigo-300"
                        title="Replay in Safe Dry-Run Mode"
                      >
                        {replayingId === r.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                        ) : (
                          <RotateCcw className="h-3.5 w-3.5 mr-1" />
                        )}
                        Replay
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Inspect Modal */}
      {inspectedRun && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="flex max-h-[90vh] w-full max-w-xl flex-col rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
              <div className="flex items-center gap-2">
                <Code2 className="h-5 w-5 text-indigo-400" />
                <h3 className="text-sm font-semibold text-slate-100">
                  Run Snapshot: {inspectedRun.event_id || inspectedRun.id}
                </h3>
              </div>
              <button
                onClick={() => setInspectedRun(null)}
                className="rounded-lg p-1 text-slate-400 hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4 text-xs">
              <div className="grid grid-cols-2 gap-3 rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                <div>
                  <span className="text-slate-500">Status: </span>
                  <span className="font-semibold text-slate-200">{inspectedRun.status}</span>
                </div>
                <div>
                  <span className="text-slate-500">Retries: </span>
                  <span className="font-semibold text-slate-200">{inspectedRun.retry_count}</span>
                </div>
                {inspectedRun.error_code && (
                  <div className="col-span-2 text-rose-400">
                    <span className="font-semibold">Error [{inspectedRun.error_code}]: </span>
                    <span>{inspectedRun.error_message}</span>
                  </div>
                )}
              </div>

              {inspectedRun.filter_result && (
                <div>
                  <label className="font-semibold text-slate-300 block mb-1">
                    Filter Evaluation Result:
                  </label>
                  <pre className="rounded-lg border border-slate-800 bg-slate-950 p-2.5 font-mono text-[11px] text-indigo-300 overflow-x-auto">
                    {JSON.stringify(inspectedRun.filter_result, null, 2)}
                  </pre>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-300 block mb-1">
                  Event Input Snapshot:
                </label>
                <pre className="rounded-lg border border-slate-800 bg-slate-950 p-2.5 font-mono text-[11px] text-emerald-300 overflow-x-auto">
                  {JSON.stringify(inspectedRun.input_snapshot, null, 2)}
                </pre>
              </div>
            </div>

            <div className="flex justify-end border-t border-slate-800 px-6 py-3">
              <Button size="sm" variant="ghost" onClick={() => setInspectedRun(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Workflow,
  History,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RotateCcw,
  ExternalLink,
  Loader2,
  Sparkles,
  GitBranch,
  Globe,
  Sliders,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { workflowService } from "@/services/workflows";
import { triggerService } from "@/services/triggers";

export default function WorkflowRunsListPage({ params }) {
  const unwrappedParams = use(params);
  const { workflowId } = unwrappedParams;

  const [workflow, setWorkflow] = useState(null);
  const [runs, setRuns] = useState([]);
  const [triggers, setTriggers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [wf, runList, trigList] = await Promise.all([
        workflowService.getWorkflow(workflowId),
        workflowService.listWorkflowRuns(workflowId, { limit: 50 }),
        triggerService.listTriggers(workflowId),
      ]);
      setWorkflow(wf);
      setRuns(runList?.runs || []);
      setTriggers(trigList?.triggers || []);
    } catch (err) {
      console.error("[WorkflowRuns] Load error:", err);
      setError(err.message || "Failed to load workflow runs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [workflowId]);

  // Helper to identify trigger source
  const getTriggerSourceBadge = (run) => {
    const execState = run.execution_state || {};
    const trigSource = execState.trigger_source || execState.trigger_type;
    const trigName = execState.trigger_name;

    if (trigSource === "schedule") {
      return (
        <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/30 gap-1 text-[11px]">
          <Clock className="h-3 w-3" />
          <span>Trigger: {trigName || "Scheduled Run"}</span>
        </Badge>
      );
    }

    if (trigSource === "connector_event" || trigSource === "github") {
      return (
        <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/30 gap-1 text-[11px]">
          <GitBranch className="h-3 w-3" />
          <span>Trigger: {trigName || "GitHub Event"}</span>
        </Badge>
      );
    }

    if (trigSource === "webhook") {
      return (
        <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/30 gap-1 text-[11px]">
          <Globe className="h-3 w-3" />
          <span>Trigger: {trigName || "Webhook Ingestion"}</span>
        </Badge>
      );
    }

    return (
      <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 gap-1 text-[11px]">
        <Play className="h-3 w-3" />
        <span>Manual Run</span>
      </Badge>
    );
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30">Completed</Badge>;
      case "running":
        return <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/30">Running</Badge>;
      case "waiting_for_approval":
      case "paused":
        return <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/30">Waiting for Approval</Badge>;
      case "failed":
        return <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/30">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
      {/* Top Header */}
      <div className="mb-6 flex flex-col gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href={`/app/workflows/${workflowId}`}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Workflow Editor</span>
            </Link>
          </div>
          <div className="mt-1 flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-white">
              {workflow?.name || "Workflow"} &mdash; Run History
            </h1>
            <Badge variant="outline" className="text-xs">
              {runs.length} Execution{runs.length === 1 ? "" : "s"}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Chronological log of all manual and automated executions for this pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href={`/app/workflows/${workflowId}/triggers`}>
            <Button variant="outline" size="sm" className="text-xs gap-1.5">
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              <span>Manage Triggers</span>
            </Button>
          </Link>
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

      {error && (
        <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Table */}
      {loading && runs.length === 0 ? (
        <div className="flex items-center justify-center p-16">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
        </div>
      ) : runs.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center border-slate-800 bg-slate-900/40">
          <History className="h-10 w-10 text-slate-600 mb-2.5" />
          <h3 className="text-sm font-semibold text-slate-200">No Workflow Runs Yet</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm">
            Execute this workflow manually from the editor or configure an automated trigger to start runs.
          </p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-950/80 uppercase text-[10px] text-slate-400 tracking-wider">
              <tr>
                <th className="px-4 py-3">Run ID</th>
                <th className="px-4 py-3">Trigger Source</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">Started At</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono font-semibold text-indigo-300">
                    <Link
                      href={`/app/workflows/${workflowId}/runs/${r.id}`}
                      className="hover:underline"
                    >
                      {r.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-4 py-3">{getTriggerSourceBadge(r)}</td>
                  <td className="px-4 py-3">{getStatusBadge(r.status)}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="text-[10px]">
                      v{r.workflow_version || 1}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {r.started_at ? new Date(r.started_at).toLocaleString() : new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-slate-300 font-mono">
                    {r.duration_ms ? `${r.duration_ms}ms` : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/app/workflows/${workflowId}/runs/${r.id}`}>
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-[11px] text-indigo-400 hover:text-indigo-300">
                        <span>Inspect</span>
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

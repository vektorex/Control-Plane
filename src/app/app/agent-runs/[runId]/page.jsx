"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import { AgentExecutionTimeline } from "@/components/agents/AgentExecutionTimeline";
import { AgentIdentityBadge } from "@/components/agents/AgentIdentityBadge";
import {
  ArrowLeft,
  Bot,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Coins,
  Cpu,
  Layers,
  ShieldCheck,
} from "lucide-react";

export default function AgentRunDetailPage({ params }) {
  const unwrappedParams = use(params);
  const { runId } = unwrappedParams;
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [run, setRun] = useState(null);
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [replaying, setReplaying] = useState(false);
  const [replayResult, setReplayResult] = useState(null);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [r, t] = await Promise.all([
        agentService.getAgentRun(runId),
        agentService.getAgentRunTrace(runId).catch(() => null),
      ]);
      setRun(r);
      setTrace(t);
    } catch (err) {
      console.error("Failed to load agent run:", err);
      setError(err.message || "Failed to load agent run details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runId) {
      loadData();
    }
  }, [runId, activeWorkspace]);

  const handleReplay = async () => {
    try {
      setReplaying(true);
      const res = await agentService.replayAgentRun(runId);
      setReplayResult(res);
    } catch (err) {
      alert(err.message || "Failed to generate replay configuration");
    } finally {
      setReplaying(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-16 rounded-xl bg-zinc-900 border border-zinc-800" />
        <div className="h-64 rounded-xl bg-zinc-900 border border-zinc-800" />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="p-8 text-center rounded-2xl border border-zinc-800 bg-zinc-950/60">
        <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-zinc-200">Run not found</h3>
        <p className="text-xs text-zinc-500 mt-1">{error || "Unable to find run"}</p>
        <Link href="/app/agents" className="mt-4 inline-block">
          <Button size="sm" variant="outline">
            Return to Agents
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800/80 pb-5">
        <div className="flex items-start gap-3">
          <Link
            href={run.agent_id ? `/app/agents/${run.agent_id}/runs` : "/app/agents"}
            className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors mt-0.5"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-zinc-100 font-mono">Run {run.id}</h1>
              <Badge
                variant={
                  run.status === "completed"
                    ? "success"
                    : run.status === "failed"
                    ? "destructive"
                    : "default"
                }
                className="capitalize text-[10px]"
              >
                {run.status}
              </Badge>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Principal Agent: <span className="font-mono text-purple-300">{run.agent_id}</span> • Version: v{run.agent_version_id?.slice(0, 8)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReplay}
            disabled={replaying}
            className="border-zinc-800 text-purple-300 hover:bg-purple-500/10 gap-1.5 text-xs"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${replaying ? "animate-spin" : ""}`} />
            <span>Dry-Run Replay</span>
          </Button>
        </div>
      </div>

      {/* Replay Result Banner */}
      {replayResult && (
        <Card className="p-4 border-purple-500/30 bg-purple-950/20 text-xs space-y-2">
          <div className="flex items-center gap-2 text-purple-300 font-semibold">
            <Sparkles className="w-4 h-4" />
            <span>Replay Metadata Generated (Dry-Run Mode: {String(replayResult.is_dry_run)})</span>
          </div>
          <pre className="p-3 rounded bg-zinc-950 border border-zinc-800 font-mono text-[11px] text-zinc-300 overflow-x-auto">
            {JSON.stringify(replayResult, null, 2)}
          </pre>
        </Card>
      )}

      {/* Execution Timeline & Telemetry */}
      <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
          <Clock className="w-4 h-4 text-purple-400" />
          <span>Execution Telemetry & Stepper</span>
        </h2>
        <AgentExecutionTimeline run={run} />
      </Card>

      {/* Input & Output */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block">
            Input Snapshot
          </span>
          <pre className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap max-h-72 overflow-y-auto">
            {JSON.stringify(run.input_snapshot, null, 2)}
          </pre>
        </Card>

        <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block">
            Final Output
          </span>
          <pre className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap max-h-72 overflow-y-auto">
            {run.output?.text || JSON.stringify(run.output, null, 2)}
          </pre>
        </Card>
      </div>

      {/* Observability Trace */}
      {trace && (
        <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <span>Trace & Span Metadata</span>
          </h2>
          <pre className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap max-h-60 overflow-y-auto">
            {JSON.stringify(trace, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}

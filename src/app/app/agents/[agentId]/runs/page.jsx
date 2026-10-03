"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import { AgentExecutionTimeline } from "@/components/agents/AgentExecutionTimeline";
import {
  ArrowLeft,
  Bot,
  History,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Layers,
  Coins,
} from "lucide-react";

export default function AgentRunsPage({ params }) {
  const unwrappedParams = use(params);
  const { agentId } = unwrappedParams;
  const { activeWorkspace } = useWorkspace();

  const [agent, setAgent] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [ag, runsList] = await Promise.all([
          agentService.getAgent(agentId),
          agentService.listAgentRuns(agentId, { limit: 50 }),
        ]);
        setAgent(ag);
        const list = Array.isArray(runsList) ? runsList : [];
        setRuns(list);
        if (list.length > 0) {
          setSelectedRun(list[0]);
        }
      } catch (err) {
        console.error("Failed to load agent runs:", err);
        setError(err.message || "Failed to load agent runs");
      } finally {
        setLoading(false);
      }
    };
    if (agentId) {
      loadData();
    }
  }, [agentId, activeWorkspace]);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-16 rounded-xl bg-zinc-900 border border-zinc-800" />
        <div className="h-64 rounded-xl bg-zinc-900 border border-zinc-800" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-zinc-800/80 pb-5">
        <Link
          href={`/app/agents/${agentId}`}
          className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-zinc-100">{agent?.name} — Execution Runs</h1>
            <Badge variant="outline" className="text-[10px] text-purple-400 border-purple-500/30">
              Audit & Trace
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Detailed timeline of bounded agent runs, token utilization, cost accounting, and step execution.
          </p>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
          No execution runs recorded for this agent yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Run List Sidebar */}
          <div className="space-y-2 lg:col-span-1">
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2">
              Recorded Runs ({runs.length})
            </span>
            <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
              {runs.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRun(r)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all text-xs space-y-1.5 ${
                    selectedRun?.id === r.id
                      ? "border-purple-500/50 bg-purple-500/10 text-purple-200"
                      : "border-zinc-800/80 bg-zinc-950/60 hover:bg-zinc-900 text-zinc-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold">
                      {r.id.slice(0, 12)}...
                    </span>
                    <Badge
                      variant={
                        r.status === "completed"
                          ? "success"
                          : r.status === "failed"
                          ? "destructive"
                          : "default"
                      }
                      className="text-[9px] uppercase px-1.5 py-0"
                    >
                      {r.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono">
                    <span>{new Date(r.created_at).toLocaleString()}</span>
                    <span>${Number(r.cost || 0).toFixed(4)}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Selected Run Details */}
          <div className="lg:col-span-2 space-y-4">
            {selectedRun ? (
              <>
                <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-zinc-100">
                        Run {selectedRun.id}
                      </span>
                      <Badge
                        variant={
                          selectedRun.status === "completed"
                            ? "success"
                            : selectedRun.status === "failed"
                            ? "destructive"
                            : "default"
                        }
                        className="text-[10px] uppercase"
                      >
                        {selectedRun.status}
                      </Badge>
                    </div>
                  </div>

                  <AgentExecutionTimeline run={selectedRun} />
                </Card>

                {/* Input Snapshot */}
                <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block">
                    Input Snapshot
                  </span>
                  <pre className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap">
                    {JSON.stringify(selectedRun.input_snapshot, null, 2)}
                  </pre>
                </Card>

                {/* Output */}
                <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block">
                    Execution Output
                  </span>
                  <pre className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap">
                    {selectedRun.output?.text || JSON.stringify(selectedRun.output, null, 2)}
                  </pre>
                </Card>
              </>
            ) : (
              <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
                Select a run on the left to inspect its timeline and outputs.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

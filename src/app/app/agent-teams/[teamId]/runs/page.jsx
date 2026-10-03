"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import { TeamRunInspector } from "@/components/agents/TeamRunInspector";
import {
  ArrowLeft,
  Boxes,
  History,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Users2,
} from "lucide-react";

export default function AgentTeamRunsPage({ params }) {
  const unwrappedParams = use(params);
  const { teamId } = unwrappedParams;
  const { activeWorkspace } = useWorkspace();

  const [team, setTeam] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [t, runsList] = await Promise.all([
        agentService.getTeam(teamId),
        agentService.listTeamRuns(teamId, { limit: 50 }),
      ]);
      setTeam(t);
      const list = Array.isArray(runsList) ? runsList : [];
      setRuns(list);
      if (list.length > 0 && !selectedRun) {
        // Fetch detailed run
        const detailed = await agentService.getTeamRun(list[0].id);
        setSelectedRun(detailed);
      }
    } catch (err) {
      console.error("Failed to load team runs:", err);
      setError(err.message || "Failed to load team runs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (teamId) {
      loadData();
    }
  }, [teamId, activeWorkspace]);

  const handleSelectRun = async (runId) => {
    try {
      const detailed = await agentService.getTeamRun(runId);
      setSelectedRun(detailed);
    } catch (err) {
      console.error("Failed to load detailed team run:", err);
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

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-zinc-800/80 pb-5">
        <Link
          href={`/app/agent-teams/${teamId}`}
          className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-zinc-100">{team?.name} — Coordinated Runs</h1>
            <Badge variant="outline" className="text-[10px] text-purple-400 border-purple-500/30">
              Multi-Agent History
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Audit inter-agent communications, parallel execution groups, peer findings, and conflict resolutions.
          </p>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
          No coordinated runs recorded for this team yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Run List Sidebar */}
          <div className="space-y-2 lg:col-span-1">
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2">
              Team Runs ({runs.length})
            </span>
            <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
              {runs.map((r) => (
                <button
                  key={r.id}
                  onClick={() => handleSelectRun(r.id)}
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
          <div className="lg:col-span-3">
            {selectedRun ? (
              <TeamRunInspector
                teamRun={selectedRun}
                onConflictResolved={() => handleSelectRun(selectedRun.id)}
              />
            ) : (
              <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
                Select a team run on the left to inspect multi-agent coordination.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

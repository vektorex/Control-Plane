"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import { AgentIdentityBadge } from "@/components/agents/AgentIdentityBadge";
import { TeamRunInspector } from "@/components/agents/TeamRunInspector";
import {
  Boxes,
  ArrowLeft,
  Play,
  Pause,
  CheckCircle2,
  Clock,
  Users2,
  Sliders,
  ShieldCheck,
  AlertCircle,
  X,
  History,
  Sparkles,
  GitBranch,
} from "lucide-react";

export default function AgentTeamDetailPage({ params }) {
  const unwrappedParams = use(params);
  const { teamId } = unwrappedParams;
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [team, setTeam] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview"); // overview, runs, settings

  // Team Run execution modal
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [runObjective, setRunObjective] = useState("");
  const [executing, setExecuting] = useState(false);
  const [activeRun, setActiveRun] = useState(null);

  const fetchTeamData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await agentService.getTeam(teamId);
      setTeam(data);
      if (data?.current_version?.objective) {
        setRunObjective(data.current_version.objective);
      }

      const runsData = await agentService.listTeamRuns(teamId, { limit: 10 });
      const runsList = Array.isArray(runsData) ? runsData : [];
      setRuns(runsList);

      if (runsList.length > 0 && !activeRun) {
        setActiveRun(runsList[0]);
      }
    } catch (err) {
      console.error("[AgentTeamDetail] Error loading team:", err);
      setError(err.message || "Failed to load multi-agent team");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (teamId) {
      fetchTeamData();
    }
  }, [teamId, activeWorkspace]);

  const handleActivate = async () => {
    try {
      setActionLoading(true);
      await agentService.activateTeam(teamId);
      await fetchTeamData();
    } catch (err) {
      alert(err.message || "Failed to activate team");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      setActionLoading(true);
      await agentService.pauseTeam(teamId);
      await fetchTeamData();
    } catch (err) {
      alert(err.message || "Failed to pause team");
    } finally {
      setActionLoading(false);
    }
  };

  const handleExecuteTeamRun = async (e) => {
    e.preventDefault();
    try {
      setExecuting(true);
      const res = await agentService.runTeam(teamId, {
        objective: runObjective,
      });
      setIsRunModalOpen(false);

      // Load the newly generated or running team run
      const detailedRun = await agentService.getTeamRun(res.id);
      setActiveRun(detailedRun);
      setActiveTab("runs");
      await fetchTeamData();
    } catch (err) {
      console.error("[AgentTeamDetail] Run execution failed:", err);
      alert(err.message || "Failed to execute team run");
    } finally {
      setExecuting(false);
    }
  };

  const handleSelectRun = async (runId) => {
    try {
      const detailed = await agentService.getTeamRun(runId);
      setActiveRun(detailed);
    } catch (err) {
      console.error("Failed to fetch team run details:", err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 rounded-xl bg-zinc-900 border border-zinc-800" />
        <div className="h-64 rounded-xl bg-zinc-900 border border-zinc-800" />
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="p-8 text-center rounded-2xl border border-zinc-800 bg-zinc-950/60">
        <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-zinc-200">Unable to load team</h3>
        <p className="text-xs text-zinc-500 mt-1">{error || "Team not found"}</p>
        <Link href="/app/agent-teams" className="mt-4 inline-block">
          <Button size="sm" variant="outline">
            Return to Teams
          </Button>
        </Link>
      </div>
    );
  }

  const currentVersion = team.current_version;
  const members = currentVersion?.members || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800/80 pb-5">
        <div className="flex items-start gap-3">
          <Link
            href="/app/agent-teams"
            className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors mt-0.5"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-zinc-100">{team.name}</h1>
              <Badge
                variant={
                  team.status === "active"
                    ? "success"
                    : team.status === "paused"
                    ? "warning"
                    : "default"
                }
                className="capitalize text-[10px]"
              >
                {team.status}
              </Badge>
            </div>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
              {team.description || currentVersion?.objective}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {team.status === "active" ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handlePause}
              disabled={actionLoading}
              className="border-zinc-800 gap-1.5"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleActivate}
              disabled={actionLoading}
              className="border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10 gap-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Activate</span>
            </Button>
          )}

          <Button
            size="sm"
            onClick={() => setIsRunModalOpen(true)}
            disabled={team.status !== "active"}
            className="bg-purple-600 hover:bg-purple-500 text-white gap-1.5"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Launch Team Run</span>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        {[
          { id: "overview", label: "Team Members & Roster" },
          { id: "runs", label: `Coordinated Runs (${runs.length})` },
          { id: "settings", label: "Team Configuration" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-purple-500 text-purple-300"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab: Roster & Policies */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Objective Banner */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Team Operational Objective (v{currentVersion?.version || 1})</span>
            </h3>
            <p className="text-xs text-zinc-300 font-sans leading-relaxed">
              {currentVersion?.objective || "No formal objective statement registered."}
            </p>
          </Card>

          {/* Members Roster */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Users2 className="w-4 h-4 text-purple-400" />
              <span>Assigned Member Principals ({members.length})</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {members.map((m, idx) => (
                <Card
                  key={m.id || idx}
                  className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AgentIdentityBadge
                          type="ai_agent"
                          name={`Agent ${m.agent_id.slice(0, 8)}`}
                          role={m.role}
                        />
                      </div>
                      <Badge variant="outline" className="text-[10px] uppercase font-mono border-zinc-800">
                        {m.role}
                      </Badge>
                    </div>

                    <div className="text-xs text-zinc-300 pt-1">
                      <span className="text-[11px] font-semibold text-zinc-400 block uppercase">
                        Responsibilities:
                      </span>
                      <p className="mt-0.5 text-zinc-300">
                        {m.responsibilities || "Standard agent task execution within granted capability boundary."}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-zinc-900 flex items-center justify-between text-[10px] text-zinc-500 font-mono">
                    <span>Agent ID: {m.agent_id.slice(0, 10)}...</span>
                    <span>Version ID: {m.agent_version_id?.slice(0, 8) || "curr"}...</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Coordination Policies */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-purple-400" />
                <span>Coordination Policy</span>
              </h3>
              <div className="space-y-1.5 text-xs font-mono text-zinc-300">
                <div>
                  Mode:{" "}
                  <span className="text-purple-300 font-semibold uppercase">
                    {currentVersion?.coordination_policy?.mode || "hierarchical"}
                  </span>
                </div>
                <div>
                  Max Parallel Agents:{" "}
                  {currentVersion?.coordination_policy?.max_parallel_agents ?? 3}
                </div>
                <div>
                  Cross Messaging:{" "}
                  {currentVersion?.coordination_policy?.allow_cross_messaging !== false
                    ? "Enabled"
                    : "Disabled"}
                </div>
              </div>
            </Card>

            <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-purple-400" />
                <span>Governance & HITL Boundaries</span>
              </h3>
              <div className="space-y-1.5 text-xs font-mono text-zinc-300">
                <div>
                  Approval Required for Final Synthesis:{" "}
                  <span
                    className={
                      currentVersion?.approval_policy?.require_human_approval_for_synthesis
                        ? "text-amber-400 font-bold"
                        : "text-zinc-400"
                    }
                  >
                    {currentVersion?.approval_policy?.require_human_approval_for_synthesis
                      ? "YES (HITL Gated)"
                      : "NO (Automated Synthesis)"}
                  </span>
                </div>
                <div>Instruction Trust: Strictly Governed</div>
                <div>Self-Approval: Prohibited</div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Runs Tab */}
      {activeTab === "runs" && (
        <div className="space-y-6">
          {runs.length === 0 ? (
            <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
              No coordinated team runs recorded yet. Click "Launch Team Run" above to execute.
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Runs Sidebar */}
              <div className="space-y-2 lg:col-span-1">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2">
                  Execution Runs
                </span>
                <div className="space-y-1.5">
                  {runs.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => handleSelectRun(r.id)}
                      className={`w-full text-left p-3 rounded-xl border transition-all text-xs space-y-1 ${
                        activeRun?.id === r.id
                          ? "border-purple-500/50 bg-purple-500/10 text-purple-200"
                          : "border-zinc-800/80 bg-zinc-950/60 hover:bg-zinc-900 text-zinc-300"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[11px] font-bold">
                          {r.id.slice(0, 10)}...
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
                      <div className="text-[10px] text-zinc-500 font-mono">
                        {new Date(r.created_at).toLocaleTimeString()}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Run Inspector */}
              <div className="lg:col-span-3">
                {activeRun ? (
                  <TeamRunInspector
                    teamRun={activeRun}
                    onConflictResolved={() => handleSelectRun(activeRun.id)}
                  />
                ) : (
                  <div className="p-8 text-center rounded-xl border border-zinc-800 text-zinc-500 text-xs">
                    Select a run to inspect execution stages and peer messages.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === "settings" && (
        <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
          <h3 className="text-sm font-semibold text-zinc-200">Team Identity & Boundaries</h3>
          <div className="space-y-3 text-xs text-zinc-300 font-mono">
            <div>Team ID: {team.id}</div>
            <div>Workspace ID: {team.workspace_id}</div>
            <div>Current Version ID: {team.current_version_id}</div>
            <div>Slug: {team.slug}</div>
            <div>Created At: {new Date(team.created_at).toISOString()}</div>
          </div>
        </Card>
      )}

      {/* Run Modal */}
      {isRunModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h3 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                <Play className="w-4 h-4 text-purple-400 fill-current" />
                <span>Launch Team Run: {team.name}</span>
              </h3>
              <button
                onClick={() => setIsRunModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleExecuteTeamRun} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">
                  Run Objective & Deliverables
                </label>
                <textarea
                  value={runObjective}
                  onChange={(e) => setRunObjective(e.target.value)}
                  rows={4}
                  className="w-full text-xs font-sans bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-purple-500"
                  required
                />
                <span className="text-[10px] text-zinc-500 block">
                  The team planner will break this objective into bounded stage assignments for each member agent.
                </span>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsRunModalOpen(false)}
                  className="border-zinc-800 text-zinc-400"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={executing}
                  className="bg-purple-600 hover:bg-purple-500 text-white gap-1.5"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{executing ? "Coordinating..." : "Execute Team Run"}</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

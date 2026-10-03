"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import { AgentIdentityBadge } from "@/components/agents/AgentIdentityBadge";
import { AgentExecutionTimeline } from "@/components/agents/AgentExecutionTimeline";
import {
  Bot,
  ArrowLeft,
  Play,
  Pause,
  CheckCircle2,
  Clock,
  Layers,
  Cpu,
  Brain,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  AlertCircle,
  X,
} from "lucide-react";

export default function AgentDetailPage() {
  const { agentId } = useParams();
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [agent, setAgent] = useState(null);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview"); // overview, versions, runs, settings

  // Run Modal State
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [runInput, setRunInput] = useState('{"task": "Analyze recent performance metrics"}');
  const [isDryRun, setIsDryRun] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [lastRun, setLastRun] = useState(null);

  const fetchAgentData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await agentService.getAgent(agentId);
      setAgent(data);

      const runsData = await agentService.listAgentRuns(agentId, { limit: 10 });
      setRuns(Array.isArray(runsData) ? runsData : []);
    } catch (err) {
      console.error("[AgentDetailPage] Error loading agent:", err);
      setError(err.message || "Failed to load agent");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (agentId) {
      fetchAgentData();
    }
  }, [agentId, activeWorkspace]);

  const handleActivate = async () => {
    try {
      setActionLoading(true);
      await agentService.activateAgent(agentId);
      await fetchAgentData();
    } catch (err) {
      alert(err.message || "Failed to activate agent");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      setActionLoading(true);
      await agentService.pauseAgent(agentId);
      await fetchAgentData();
    } catch (err) {
      alert(err.message || "Failed to pause agent");
    } finally {
      setActionLoading(false);
    }
  };

  const handleExecuteRun = async (e) => {
    e.preventDefault();
    try {
      setExecuting(true);
      let parsedInput = {};
      try {
        parsedInput = JSON.parse(runInput);
      } catch {
        parsedInput = { prompt: runInput };
      }

      const run = await agentService.runAgent(agentId, {
        input: parsedInput,
        dry_run: isDryRun,
      });
      setLastRun(run);
      setIsRunModalOpen(false);
      await fetchAgentData();
    } catch (err) {
      alert(err.message || "Failed to execute agent run");
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto py-8">
        <div className="h-8 w-48 bg-zinc-800 rounded animate-pulse" />
        <div className="h-64 bg-zinc-900/40 rounded-xl border border-zinc-800 animate-pulse" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="p-8 text-center max-w-lg mx-auto space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h2 className="text-lg font-semibold text-zinc-200">Agent not found</h2>
        <p className="text-xs text-zinc-400">{error || "Could not retrieve the requested agent."}</p>
        <Link href="/app/agents">
          <Button variant="outline" size="sm">
            Back to Agents
          </Button>
        </Link>
      </div>
    );
  }

  const currentVersion = agent.current_version;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800/80 pb-5">
        <div className="flex items-start gap-3">
          <Link
            href="/app/agents"
            className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors mt-0.5"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-zinc-100">{agent.name}</h1>
              <Badge
                variant={
                  agent.status === "active"
                    ? "success"
                    : agent.status === "paused"
                    ? "warning"
                    : "default"
                }
                className="capitalize text-[10px]"
              >
                {agent.status}
              </Badge>
            </div>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl">{agent.purpose}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {agent.status === "active" ? (
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
            disabled={agent.status !== "active"}
            className="bg-purple-600 hover:bg-purple-500 text-white gap-1.5"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run Agent</span>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800">
        {[
          { id: "overview", label: "Overview & Policies" },
          { id: "runs", label: `Runs (${runs.length})` },
          { id: "settings", label: "Identity & Configuration" },
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

      {/* Tab Panels */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Identity Tag */}
          <div className="flex items-center justify-between p-4 rounded-xl border border-zinc-800 bg-zinc-950/70">
            <div className="flex items-center gap-3">
              <AgentIdentityBadge
                type="ai_agent"
                name={agent.name}
                versionNumber={currentVersion?.version || 1}
              />
              <span className="text-xs text-zinc-400 font-mono">
                Principal ID: {agent.id.slice(0, 13)}...
              </span>
            </div>
            <span className="text-xs text-zinc-500 font-mono">
              Created: {new Date(agent.created_at).toLocaleDateString()}
            </span>
          </div>

          {/* Policies Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Capabilities */}
            <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-purple-400" />
                <span>Granted Capabilities</span>
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {(currentVersion?.capability_policy || []).map((cap) => (
                  <span
                    key={cap}
                    className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono text-[11px]"
                  >
                    {cap}
                  </span>
                ))}
              </div>
            </Card>

            {/* Model Policy */}
            <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>Model Policy</span>
              </h3>
              <div className="space-y-1.5 text-xs font-mono text-zinc-300">
                <div>
                  Preferred Model:{" "}
                  <span className="text-purple-300 font-semibold">
                    {currentVersion?.model_policy?.preferred_model || "gpt-4o-mini"}
                  </span>
                </div>
                <div>Temperature: {currentVersion?.model_policy?.temperature ?? 0.2}</div>
                <div>Max Output Tokens: {currentVersion?.model_policy?.max_output_tokens || 2048}</div>
              </div>
            </Card>
          </div>

          {/* System Instructions */}
          <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Immutable Version Instructions (v{currentVersion?.version || 1})</span>
            </h3>
            <pre className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300 whitespace-pre-wrap">
              {currentVersion?.instructions || "No custom instructions declared."}
            </pre>
          </Card>

          {/* Last Run Preview if executed */}
          {lastRun && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Latest Execution Run Result
              </h3>
              <AgentExecutionTimeline run={lastRun} />
            </div>
          )}
        </div>
      )}

      {/* Runs Tab */}
      {activeTab === "runs" && (
        <div className="space-y-4">
          {runs.length === 0 ? (
            <div className="p-12 text-center rounded-2xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
              No execution runs recorded for this agent yet.
            </div>
          ) : (
            <div className="space-y-3">
              {runs.map((r) => (
                <div
                  key={r.id}
                  className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/70 space-y-3"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-purple-400 font-bold">
                        {r.id.slice(0, 13)}...
                      </span>
                      <Badge
                        variant={
                          r.status === "completed"
                            ? "success"
                            : r.status === "failed"
                            ? "destructive"
                            : "default"
                        }
                        className="text-[10px] capitalize"
                      >
                        {r.status}
                      </Badge>
                    </div>
                    <span className="text-zinc-500 font-mono">
                      {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>

                  <AgentExecutionTimeline run={r} />

                  {r.output && (
                    <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-300 space-y-1">
                      <span className="font-semibold text-zinc-400 block text-[11px] uppercase">
                        Output:
                      </span>
                      <p className="font-sans whitespace-pre-wrap">{r.output.text || JSON.stringify(r.output)}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === "settings" && (
        <Card className="p-5 border-zinc-800 bg-zinc-950/70 space-y-4">
          <h3 className="text-sm font-semibold text-zinc-200">Agent Configuration</h3>
          <div className="space-y-3 text-xs text-zinc-300 font-mono">
            <div>Agent ID: {agent.id}</div>
            <div>Workspace ID: {agent.workspace_id}</div>
            <div>Current Version ID: {agent.current_version_id}</div>
            <div>Slug: {agent.slug}</div>
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
                <span>Run Agent: {agent.name}</span>
              </h3>
              <button
                onClick={() => setIsRunModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleExecuteRun} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">
                  Task Input (JSON or Plain Text)
                </label>
                <textarea
                  value={runInput}
                  onChange={(e) => setRunInput(e.target.value)}
                  rows={4}
                  className="w-full text-xs p-3 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-200 font-mono focus:outline-none focus:border-purple-500"
                  required
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="dryRunToggle"
                  checked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-900 text-purple-600 focus:ring-0"
                />
                <label htmlFor="dryRunToggle" className="text-xs text-zinc-300 cursor-pointer">
                  Dry-Run Mode (Simulation without external side effects)
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-zinc-900">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsRunModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={executing}
                  className="bg-purple-600 hover:bg-purple-500 text-white"
                >
                  {executing ? "Dispatching..." : "Execute Run"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

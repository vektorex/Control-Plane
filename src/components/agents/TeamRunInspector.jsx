"use client";

import React, { useState } from "react";
import {
  Boxes,
  CheckCircle2,
  Clock,
  AlertOctagon,
  FileText,
  Layers,
  Sparkles,
  GitBranch,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AgentIdentityBadge } from "./AgentIdentityBadge";
import { AgentMessageThread } from "./AgentMessageThread";

/**
 * TeamRunInspector: Comprehensive multi-agent team execution inspector.
 * Visualizes objective, plan assignments, shared context, messages, conflicts, and final synthesis.
 */
export function TeamRunInspector({ teamRun, onResolveConflict, className = "" }) {
  const [activeTab, setActiveTab] = useState("overview"); // overview, assignments, messages, conflicts, synthesis
  const [resolvingId, setResolvingId] = useState(null);
  const [resolutionText, setResolutionText] = useState("");

  if (!teamRun) return null;

  const plan = teamRun.plan || {};
  const assignments = plan.assignments || [];
  const parallelGroups = plan.parallel_groups || [];
  const messages = teamRun.messages || [];
  const conflicts = teamRun.conflicts || [];
  const synthesis = teamRun.final_synthesis;

  const handleResolve = async (conflictId) => {
    if (!onResolveConflict || !resolutionText.trim()) return;
    await onResolveConflict(conflictId, {
      status: "resolved_by_human",
      resolution: resolutionText,
    });
    setResolvingId(null);
    setResolutionText("");
  };

  return (
    <div className={cn("rounded-xl border border-zinc-800 bg-zinc-950/80 overflow-hidden space-y-4", className)}>
      {/* Header Summary */}
      <div className="p-5 border-b border-zinc-800 bg-zinc-900/40 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Boxes className="w-5 h-5 text-purple-400" />
            <h3 className="text-base font-semibold text-zinc-100">Team Run Coordination</h3>
            <span
              className={cn(
                "px-2 py-0.5 rounded text-xs uppercase font-mono tracking-wider border",
                teamRun.status === "completed"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : teamRun.status === "failed"
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  : "bg-purple-500/10 text-purple-400 border-purple-500/30"
              )}
            >
              {teamRun.status}
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl font-mono">
            Objective: {teamRun.objective}
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
          <div>
            <span className="text-zinc-500">Cost: </span>
            <span className="text-zinc-200">${Number(teamRun.cost || 0).toFixed(4)}</span>
          </div>
          <div>
            <span className="text-zinc-500">Latency: </span>
            <span className="text-zinc-200">{teamRun.latency ? `${teamRun.latency}s` : "0.0s"}</span>
          </div>
          <div>
            <span className="text-zinc-500">Messages: </span>
            <span className="text-zinc-200">{messages.length}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-5 flex gap-2 border-b border-zinc-800/80">
        {[
          { id: "overview", label: "Overview & Stages", count: parallelGroups.length },
          { id: "assignments", label: "Assignments", count: assignments.length },
          { id: "messages", label: "Agent Messages", count: messages.length },
          { id: "conflicts", label: "Conflicts", count: conflicts.length, alert: conflicts.some((c) => c.status === "open") },
          { id: "synthesis", label: "Final Synthesis", count: synthesis ? 1 : 0 },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-3 py-2 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5",
              activeTab === tab.id
                ? "border-purple-500 text-purple-300"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            )}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={cn(
                  "px-1.5 py-0.2 rounded-full text-[10px] font-mono",
                  tab.alert
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                    : "bg-zinc-800 text-zinc-400"
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="p-5 pt-1">
        {/* 1. Overview */}
        {activeTab === "overview" && (
          <div className="space-y-4">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Coordinated Execution Groups
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {parallelGroups.map((group, gIdx) => (
                <div
                  key={gIdx}
                  className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-900/30 space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-zinc-300">
                      Stage {gIdx + 1} ({group.length > 1 ? "Parallel Group" : "Single Agent"})
                    </span>
                    <span className="text-[11px] text-zinc-500 font-mono">
                      {group.length} Assigned Agent(s)
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {group.map((agId) => (
                      <AgentIdentityBadge
                        key={agId}
                        type="ai_agent"
                        name={agId.slice(0, 8)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Shared context snapshot */}
            <div className="p-3.5 rounded-lg border border-zinc-800 bg-zinc-900/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-zinc-300">
                <FileText className="w-4 h-4 text-purple-400" />
                <span>Team Shared Context</span>
              </div>
              <pre className="p-3 rounded bg-black/40 text-[11px] font-mono text-zinc-400 overflow-x-auto max-h-48 border border-zinc-800/50">
                {JSON.stringify(teamRun.shared_context || {}, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* 2. Assignments */}
        {activeTab === "assignments" && (
          <div className="space-y-2.5">
            {assignments.map((assign, idx) => (
              <div
                key={assign.assignment_id || idx}
                className="p-3.5 rounded-lg border border-zinc-800 bg-zinc-900/30 flex flex-wrap items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-purple-400 font-bold">
                      #{assign.assignment_id}
                    </span>
                    <AgentIdentityBadge
                      type="ai_agent"
                      name={assign.agent_id ? assign.agent_id.slice(0, 8) : "Agent"}
                    />
                    <span className="text-zinc-400 font-medium capitalize">
                      Stage {assign.stage} • {assign.type?.replace(/_/g, " ")}
                    </span>
                  </div>
                  <p className="text-zinc-300 text-xs pl-0.5">{assign.description}</p>
                </div>
                {assign.dependencies && assign.dependencies.length > 0 && (
                  <div className="text-[11px] text-zinc-500 font-mono">
                    Depends on: {assign.dependencies.map((d) => d.slice(0, 6)).join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 3. Messages */}
        {activeTab === "messages" && <AgentMessageThread messages={messages} />}

        {/* 4. Conflicts */}
        {activeTab === "conflicts" && (
          <div className="space-y-3">
            {conflicts.length === 0 ? (
              <div className="p-6 text-center rounded-xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
                No discrepancies or conflicts detected between team members.
              </div>
            ) : (
              conflicts.map((conf) => (
                <div
                  key={conf.id}
                  className="p-4 rounded-lg border border-rose-500/20 bg-rose-500/5 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0" />
                      <span className="text-xs font-semibold text-rose-300">
                        {conf.subject}
                      </span>
                    </div>
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-[10px] uppercase font-mono tracking-wider border",
                        conf.status === "open"
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                          : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                      )}
                    >
                      {conf.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800 space-y-1">
                      <span className="text-[11px] text-zinc-400 font-mono">
                        Position A (Agent {conf.agent_a_id?.slice(0, 8)}):
                      </span>
                      <p className="text-zinc-200">{conf.position_a}</p>
                    </div>
                    <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800 space-y-1">
                      <span className="text-[11px] text-zinc-400 font-mono">
                        Position B (Agent {conf.agent_b_id?.slice(0, 8)}):
                      </span>
                      <p className="text-zinc-200">{conf.position_b}</p>
                    </div>
                  </div>

                  {conf.status === "open" ? (
                    <div>
                      {resolvingId === conf.id ? (
                        <div className="space-y-2 pt-1">
                          <textarea
                            value={resolutionText}
                            onChange={(e) => setResolutionText(e.target.value)}
                            placeholder="Enter human arbitration resolution..."
                            rows={2}
                            className="w-full text-xs p-2 rounded bg-zinc-900 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-purple-500"
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleResolve(conf.id)}
                              className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-medium"
                            >
                              Submit Resolution
                            </button>
                            <button
                              onClick={() => setResolvingId(null)}
                              className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-xs"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setResolvingId(conf.id)}
                          className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded text-xs font-medium border border-zinc-700"
                        >
                          Arbitrate / Resolve Discrepancy
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-zinc-400 p-2.5 rounded bg-zinc-900/40 border border-zinc-800">
                      <strong>Resolution:</strong> {conf.resolution}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* 5. Synthesis */}
        {activeTab === "synthesis" && (
          <div className="space-y-3">
            {synthesis ? (
              <div className="p-4 rounded-lg border border-purple-500/20 bg-purple-500/5 space-y-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-purple-300">
                    Final Multi-Agent Synthesis
                  </h4>
                </div>
                <p className="text-xs text-zinc-200 leading-relaxed font-sans">
                  {synthesis.summary}
                </p>

                {synthesis.member_contributions && (
                  <div className="space-y-2 pt-2 border-t border-purple-500/10">
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                      Verified Member Contributions:
                    </span>
                    <div className="space-y-1.5">
                      {Object.entries(synthesis.member_contributions).map(([agId, text]) => (
                        <div
                          key={agId}
                          className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800/80 text-xs flex items-start gap-2"
                        >
                          <AgentIdentityBadge type="ai_agent" name={agId.slice(0, 8)} />
                          <span className="text-zinc-300 pt-0.5">{text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center rounded-xl border border-zinc-800 bg-zinc-950/40 text-zinc-500 text-xs">
                Final synthesis not yet generated for this team run.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

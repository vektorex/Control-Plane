"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FlaskConical,
  Play,
  Square,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Shield,
  Eye,
} from "lucide-react";
import { reliabilityService } from "@/services/reliability";

export function ChaosExperimentTable({ experiments = [], onRefresh }) {
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [safetySummary, setSafetySummary] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [execMessage, setExecMessage] = useState("");

  const handleInspectSafety = async (exp) => {
    try {
      setSelectedExperiment(exp);
      const summary = await reliabilityService.getExperimentSafetySummary(exp.id);
      setSafetySummary(summary);
    } catch (err) {
      alert("Failed to load safety summary: " + (err.message || err));
    }
  };

  const handleRun = async (expId) => {
    try {
      setIsExecuting(true);
      setExecMessage("Executing sandbox failure injection...");
      await reliabilityService.runExperiment(expId);
      setExecMessage("Chaos experiment completed safely.");
      setTimeout(() => {
        setIsExecuting(false);
        setSelectedExperiment(null);
        setSafetySummary(null);
        if (onRefresh) onRefresh();
      }, 1000);
    } catch (err) {
      alert("Execution failed: " + (err.message || err));
      setIsExecuting(false);
    }
  };

  const handleAbort = async (expId) => {
    if (!confirm("Are you sure you want to abort this chaos experiment?")) return;
    try {
      await reliabilityService.abortExperiment(expId, "Operator manual abort");
      if (onRefresh) onRefresh();
    } catch (err) {
      alert("Failed to abort: " + (err.message || err));
    }
  };

  const getStatusBadge = (st) => {
    switch (st) {
      case "completed":
        return <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-medium">Completed</span>;
      case "running":
        return <span className="text-xs px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-800 font-medium animate-pulse">Running</span>;
      case "approved":
        return <span className="text-xs px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-medium">Approved</span>;
      case "aborted":
        return <span className="text-xs px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800 font-medium">Aborted</span>;
      default:
        return <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">{st}</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-purple-400" />
            Chaos & Resilience Experiments ({experiments.length})
          </h3>
          <p className="text-xs text-slate-500">
            Controlled failure simulations testing recovery assumptions without customer data damage.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Experiment Name</th>
              <th className="py-3 px-4 font-semibold">Environment</th>
              <th className="py-3 px-4 font-semibold">Target Subsystem</th>
              <th className="py-3 px-4 font-semibold">Failure Injection</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {experiments.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                  No chaos experiments configured. Create a sandbox experiment to test resilience.
                </td>
              </tr>
            ) : (
              experiments.map((exp) => (
                <tr key={exp.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{exp.name}</div>
                    <div className="text-[11px] text-slate-500 truncate max-w-xs">{exp.description}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-mono uppercase ${
                        exp.environment === "production"
                          ? "bg-red-950 text-red-400 border border-red-800 font-bold"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {exp.environment}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-mono text-slate-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {exp.target_type}/{exp.target_id}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-mono text-purple-300">
                      {exp.failure_type}
                    </span>
                    <span className="text-slate-500 text-[11px] ml-1">({exp.duration_seconds}s)</span>
                  </td>
                  <td className="py-3 px-4">{getStatusBadge(exp.status)}</td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => handleInspectSafety(exp)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                      title="Inspect Blast Radius Safety Summary"
                    >
                      <Shield className="w-3.5 h-3.5 text-indigo-400" />
                      Safety
                    </button>

                    {exp.status === "running" ? (
                      <button
                        onClick={() => handleAbort(exp.id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded bg-red-950 hover:bg-red-900 text-red-300 border border-red-800"
                      >
                        <Square className="w-3 h-3" /> Abort
                      </button>
                    ) : (
                      <button
                        onClick={() => handleInspectSafety(exp)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-purple-600 hover:bg-purple-500 text-white"
                      >
                        <Play className="w-3 h-3" /> Run
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Safety Summary & Execution Confirmation Modal */}
      {selectedExperiment && safetySummary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/40 text-purple-400">
                  <FlaskConical className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Blast Radius Safety Summary</h3>
                  <p className="text-xs text-slate-500">{selectedExperiment.name}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedExperiment(null);
                  setSafetySummary(null);
                }}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500 block">Environment</span>
                  <span className="text-white font-mono font-bold uppercase">
                    {safetySummary.environment}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Target Type</span>
                  <span className="text-white font-mono">{safetySummary.target_type}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Failure Action</span>
                  <span className="text-purple-300 font-mono">{safetySummary.failure_type}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Duration</span>
                  <span className="text-white font-mono">{safetySummary.duration_seconds} seconds</span>
                </div>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-400 font-semibold block">Declared Blast Radius:</span>
                <p className="text-slate-300 leading-relaxed">{safetySummary.blast_radius}</p>
              </div>

              {safetySummary.is_production && (
                <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-red-300 space-y-1">
                  <div className="flex items-center gap-2 font-bold">
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    Production Chaos Notice
                  </div>
                  <p className="text-[11px]">
                    Production failure injection strictly requires Step 32 Governance authorization and
                    Step 18 HITL human approval.
                  </p>
                </div>
              )}

              {execMessage && (
                <div className="p-2.5 bg-purple-950/40 border border-purple-800 rounded text-purple-300 text-center font-mono">
                  {execMessage}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedExperiment(null);
                    setSafetySummary(null);
                  }}
                  className="px-4 py-2 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-white"
                >
                  Close
                </button>

                <button
                  onClick={() => handleRun(selectedExperiment.id)}
                  disabled={isExecuting}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" />
                  {isExecuting ? "Executing..." : "Confirm & Run Experiment"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

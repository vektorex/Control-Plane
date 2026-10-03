"use client";

import React, { useState } from "react";
import { Play, Pause, RotateCw, XCircle, ShieldAlert, Cpu, Sparkles, CheckCircle2 } from "lucide-react";

export function CoExecutionPanel({
  session,
  activeRun,
  onInitiateRun,
  onPauseRun,
  onResumeRun,
  onCancelRun,
}) {
  const [mode, setMode] = useState("human_assisted");
  const [includeComments, setIncludeComments] = useState(true);
  const [includeAnnotations, setIncludeAnnotations] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const handleStart = async () => {
    setSubmitting(true);
    try {
      await onInitiateRun({
        mode,
        include_comments: includeComments,
        include_annotations: includeAnnotations,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "executing":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "awaiting_approval":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "awaiting_input":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      case "completed":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      case "cancelled":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Human + AI Co-Execution</h3>
            <p className="text-[11px] text-slate-500">Collaborative run lifecycle and shared instruction control</p>
          </div>
        </div>

        {activeRun && (
          <span className={`px-2.5 py-0.5 rounded-full border text-xs font-semibold uppercase tracking-wider ${getStatusBadge(activeRun.status)}`}>
            {activeRun.status}
          </span>
        )}
      </div>

      {/* Trust Hierarchy Notice */}
      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-amber-300 text-xs">
        <ShieldAlert className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
        <div>
          <span className="font-semibold">Instruction Trust Hierarchy Enforced:</span> Authoritative task
          instructions and governance policies take precedence. Comments provide supplemental context only and cannot
          override authoritative instructions. AI suggestions do not count as human approval.
        </div>
      </div>

      {/* Active Run Controls */}
      {activeRun ? (
        <div className="flex flex-col gap-3 p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Run ID: <code className="text-slate-300 font-mono">{activeRun.id.slice(0, 12)}...</code></span>
            <span className="text-slate-400">Mode: <span className="font-semibold text-indigo-400">{activeRun.mode}</span></span>
          </div>

          <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
            {activeRun.status === "executing" && onPauseRun && (
              <button
                onClick={() => onPauseRun(activeRun.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
              >
                <Pause className="w-3.5 h-3.5 text-amber-400" />
                <span>Pause</span>
              </button>
            )}

            {activeRun.status === "awaiting_input" && onResumeRun && (
              <button
                onClick={() => onResumeRun(activeRun.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
            )}

            {onCancelRun && activeRun.status !== "completed" && activeRun.status !== "cancelled" && (
              <button
                onClick={() => onCancelRun(activeRun.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/30 text-rose-300 text-xs font-medium transition-colors ml-auto"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Cancel Run</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Run Configuration & Dispatch */
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { id: "human_assisted", label: "Human Assisted", desc: "AI draft with human checks" },
              { id: "ai_assisted", label: "AI Assisted", desc: "Human primary with AI assist" },
              { id: "review_before_execute", label: "Review Before Run", desc: "Mandatory human sign-off" },
              { id: "shared_execution", label: "Shared Co-Run", desc: "Concurrent human & AI execution" },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMode(m.id)}
                className={`flex flex-col p-2.5 rounded-lg border text-left transition-all ${
                  mode === m.id
                    ? "bg-indigo-500/10 border-indigo-500 text-white"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <span className="font-semibold text-slate-200">{m.label}</span>
                <span className="text-[10px] text-slate-500">{m.desc}</span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-300 pt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeComments}
                onChange={(e) => setIncludeComments(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
              />
              <span>Include approved comments</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeAnnotations}
                onChange={(e) => setIncludeAnnotations(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
              />
              <span>Include active annotations</span>
            </label>
          </div>

          <button
            onClick={handleStart}
            disabled={submitting}
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>Launch Collaborative AI Execution</span>
          </button>
        </div>
      )}
    </div>
  );
}

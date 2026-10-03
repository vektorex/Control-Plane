"use client";

import React from "react";
import { CheckCircle2, Clock, AlertTriangle, XCircle, ArrowRight, ShieldCheck, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * AgentExecutionTimeline: Visualizes state transitions, bounded steps, tokens, cost, and latency.
 */
export function AgentExecutionTimeline({ run, className = "" }) {
  if (!run) return null;

  const states = [
    { key: "created", label: "Created" },
    { key: "planning", label: "Planning" },
    { key: "executing", label: "Executing" },
    { key: "evaluating", label: "Evaluating" },
    { key: "completed", label: "Completed" },
  ];

  const currentState = run.status || "created";
  const isFailed = currentState === "failed";
  const isWaitingApproval = currentState === "waiting_for_approval";

  return (
    <div className={cn("p-4 rounded-xl border border-zinc-800 bg-zinc-950/70 space-y-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-purple-400" />
          <h4 className="text-sm font-semibold text-zinc-100">Execution Lifecycle</h4>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-zinc-400">
          <span>Cost: ${Number(run.cost || 0).toFixed(4)}</span>
          <span>•</span>
          <span>Latency: {run.latency ? `${run.latency}s` : "0.0s"}</span>
          <span>•</span>
          <span>Tokens: {run.tokens?.total_tokens || 0}</span>
        </div>
      </div>

      {/* Progress Stepper */}
      <div className="relative flex items-center justify-between py-2">
        {states.map((st, idx) => {
          const isDone =
            currentState === "completed" ||
            (states.findIndex((s) => s.key === currentState) >= idx && !isFailed);
          const isCurrent = currentState === st.key;

          return (
            <div key={st.key} className="flex-1 flex flex-col items-center relative z-10">
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all border",
                  isDone
                    ? "bg-purple-500/20 text-purple-300 border-purple-500/50"
                    : isCurrent
                    ? "bg-purple-600 text-white border-purple-400 shadow-lg shadow-purple-500/30 animate-pulse"
                    : "bg-zinc-900 text-zinc-600 border-zinc-800"
                )}
              >
                {isDone ? <CheckCircle2 className="w-4 h-4 text-purple-400" /> : idx + 1}
              </div>
              <span className="text-[11px] font-medium text-zinc-400 mt-1.5 capitalize">
                {st.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Exception alerts if failed or waiting for HITL */}
      {isWaitingApproval && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Execution paused: Human-in-the-Loop review required for privileged action.</span>
        </div>
      )}

      {isFailed && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Execution Failed:</span>{" "}
            <span>{run.error?.message || "An unexpected error occurred during execution."}</span>
          </div>
        </div>
      )}
    </div>
  );
}

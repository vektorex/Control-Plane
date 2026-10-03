"use client";

import React from "react";
import Link from "next/link";
import {
  FlaskConical,
  Play,
  Square,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from "lucide-react";

export function RecoveryExerciseTable({
  exercises = [],
  onRun,
  onAbort,
  onRefresh,
}) {
  const getStatusBadge = (st) => {
    switch (st) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3 h-3" /> Completed
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800 animate-pulse">
            <Clock className="w-3 h-3" /> Running
          </span>
        );
      case "planned":
        return (
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
            Planned
          </span>
        );
      case "aborted":
        return (
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
            Aborted
          </span>
        );
      default:
        return (
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            {st}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FlaskConical className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">Disaster Recovery Exercises & Drills</h3>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {exercises.length} exercises recorded
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Exercise Name</th>
              <th className="py-3 px-4 font-semibold">Scenario</th>
              <th className="py-3 px-4 font-semibold">Environment</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Created At</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {exercises.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 text-xs font-sans">
                  No recovery exercises planned. Create a drill in sandbox/staging to simulate recovery.
                </td>
              </tr>
            ) : (
              exercises.map((ex) => (
                <tr key={ex.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{ex.name}</div>
                    <div className="text-[11px] text-slate-500 truncate max-w-xs">
                      {ex.description || "Simulation drill"}
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-indigo-300">
                    {ex.scenario.replace(/_/g, " ")}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs uppercase">
                    <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300">
                      {ex.environment}
                    </span>
                  </td>
                  <td className="py-3 px-4">{getStatusBadge(ex.status)}</td>
                  <td className="py-3 px-4 text-xs text-slate-400 font-mono">
                    {new Date(ex.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {ex.status === "planned" && onRun && (
                        <button
                          onClick={() => onRun(ex.id)}
                          className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-sm transition"
                        >
                          <Play className="w-3 h-3" /> Run
                        </button>
                      )}

                      {ex.status === "running" && onAbort && (
                        <button
                          onClick={() => onAbort(ex.id)}
                          className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-red-600 hover:bg-red-500 text-white font-medium shadow-sm transition"
                        >
                          <Square className="w-3 h-3" /> Abort
                        </button>
                      )}

                      <Link
                        href={`/app/recovery/exercises/${ex.id}`}
                        className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium p-1"
                      >
                        Inspect <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

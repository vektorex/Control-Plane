"use client";

import React from "react";
import {
  LifeBuoy,
  ShieldCheck,
  AlertTriangle,
  Archive,
  RotateCcw,
  Clock,
  Layers,
  FlaskConical,
} from "lucide-react";

export function RecoveryOverviewCards({ overview }) {
  if (!overview) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="p-5 bg-slate-900 border border-slate-800 rounded-xl animate-pulse h-28" />
        ))}
      </div>
    );
  }

  const isReady = overview.recovery_readiness_status === "ready";
  const isBlocked = overview.recovery_readiness_status === "blocked";
  const isStale = overview.stale_backups > 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Readiness State */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Recovery Readiness
          </span>
          <LifeBuoy className={`w-4 h-4 ${isReady ? "text-emerald-400" : isBlocked ? "text-red-400" : "text-amber-400"}`} />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className={`text-xl font-bold uppercase font-mono ${isReady ? "text-emerald-400" : isBlocked ? "text-red-400" : "text-amber-400"}`}>
            {overview.recovery_readiness_status}
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1 font-mono">
          {overview.open_recovery_blockers} active recovery blocker(s)
        </p>
      </div>

      {/* 2. Backup Integrity */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Verified Snapshots
          </span>
          <ShieldCheck className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white font-mono">
            {overview.verified_backups}
          </span>
          <span className="text-xs text-slate-500 font-mono">
            / {overview.completed_backups} completed
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          {overview.total_backups} total snapshots recorded
        </p>
      </div>

      {/* 3. Freshness & Staleness */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Backup Freshness
          </span>
          {isStale ? (
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          ) : (
            <Clock className="w-4 h-4 text-emerald-400" />
          )}
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className={`text-sm font-mono font-bold ${isStale ? "text-amber-400" : "text-slate-200"}`}>
            {overview.last_backup_at
              ? new Date(overview.last_backup_at).toLocaleDateString()
              : "No Backups"}
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1 font-mono">
          {overview.stale_backups > 0 ? "Stale: exceeds 24h RPO" : "Fresh: within RPO window"}
        </p>
      </div>

      {/* 4. Restore & Exercises */}
      <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Restores & Drills
          </span>
          <RotateCcw className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white font-mono">
            {overview.recent_restores_count}
          </span>
          <span className="text-xs text-slate-500 font-mono">
            restores • {overview.completed_exercises_count} exercises
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1 font-mono">
          {overview.active_policies} active backup policy schedules
        </p>
      </div>
    </div>
  );
}

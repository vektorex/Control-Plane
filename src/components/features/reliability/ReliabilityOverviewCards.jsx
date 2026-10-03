"use client";

import React from "react";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Zap,
  Bookmark,
  FlaskConical,
  Cpu,
} from "lucide-react";

export function ReliabilityOverviewCards({ overview, telemetry }) {
  const healthy = overview?.healthy_components ?? 0;
  const degraded = overview?.degraded_components ?? 0;
  const unavailable = overview?.unavailable_components ?? 0;
  const activeCheckpoints = overview?.active_checkpoints ?? 0;
  const openCircuits = overview?.active_circuit_breakers_open ?? 0;
  const chaosActive = overview?.chaos_experiments_active ?? 0;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Healthy Components */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Healthy Components
            </span>
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800/40 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-emerald-400 tracking-tight">
              {healthy}
            </span>
            <span className="text-xs text-slate-500">fully operational</span>
          </div>
        </div>

        {/* Degraded */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Degraded
            </span>
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-800/40 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-400 tracking-tight">
              {degraded}
            </span>
            <span className="text-xs text-slate-500">partial capability</span>
          </div>
        </div>

        {/* Unavailable */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Unavailable
            </span>
            <div className="p-2 rounded-lg bg-red-950/60 border border-red-800/40 text-red-400">
              <XCircle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-red-400 tracking-tight">
              {unavailable}
            </span>
            <span className="text-xs text-slate-500">critical outage</span>
          </div>
        </div>

        {/* Open Circuit Breakers */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Open Circuits
            </span>
            <div className="p-2 rounded-lg bg-orange-950/60 border border-orange-800/40 text-orange-400">
              <Zap className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-orange-400 tracking-tight">
              {openCircuits}
            </span>
            <span className="text-xs text-slate-500">fast-failing</span>
          </div>
        </div>

        {/* Active Checkpoints */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Checkpoints
            </span>
            <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-800/40 text-blue-400">
              <Bookmark className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">
              {activeCheckpoints}
            </span>
            <span className="text-xs text-slate-500">resumable state</span>
          </div>
        </div>

        {/* Chaos Experiments */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Active Chaos
            </span>
            <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/40 text-purple-400">
              <FlaskConical className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-purple-400 tracking-tight">
              {chaosActive}
            </span>
            <span className="text-xs text-slate-500">sandbox runs</span>
          </div>
        </div>
      </div>

      {/* Telemetry Summary Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs">
        <div className="flex items-center justify-between px-2">
          <span className="text-slate-400">Availability (30d):</span>
          <strong className="text-emerald-400 font-mono">
            {telemetry?.overall_availability_pct ?? 100}%
          </strong>
        </div>
        <div className="flex items-center justify-between px-2 border-l border-slate-800">
          <span className="text-slate-400">Avg Check Latency:</span>
          <strong className="text-white font-mono">
            {telemetry?.average_latency_ms ?? 0} ms
          </strong>
        </div>
        <div className="flex items-center justify-between px-2 border-l border-slate-800">
          <span className="text-slate-400">Recent Failures (24h):</span>
          <strong className="text-amber-400 font-mono">
            {overview?.recent_failures_24h ?? 0}
          </strong>
        </div>
        <div className="flex items-center justify-between px-2 border-l border-slate-800">
          <span className="text-slate-400">Total Checks:</span>
          <strong className="text-slate-300 font-mono">
            {telemetry?.total_checks ?? 0}
          </strong>
        </div>
      </div>
    </div>
  );
}

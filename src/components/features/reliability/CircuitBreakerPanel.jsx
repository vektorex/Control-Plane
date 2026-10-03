"use client";

import React from "react";
import {
  ShieldAlert,
  Zap,
  Activity,
  Layers,
  CheckCircle,
  AlertOctagon,
  Clock,
  RefreshCw,
} from "lucide-react";

export function CircuitBreakerPanel({
  circuits = {},
  bulkheads = {},
  onRefresh,
}) {
  const circuitEntries = Object.entries(circuits);
  const bulkheadEntries = Object.entries(bulkheads);

  const getCircuitBadge = (state) => {
    switch (state) {
      case "closed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
            <CheckCircle className="w-3 h-3" /> Closed (Passing)
          </span>
        );
      case "half_open":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/80 animate-pulse">
            <Clock className="w-3 h-3" /> Half-Open (Testing)
          </span>
        );
      case "open":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-red-950/80 text-red-400 border border-red-800/80">
            <AlertOctagon className="w-3 h-3" /> Open (Tripped)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-400">
            {state || "unknown"}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Circuit Breakers Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-semibold text-white">External Dependency Circuit Breakers</h3>
              <p className="text-xs text-slate-400">
                Non-database external boundaries (AI providers, connectors, tools) with trip protection
              </p>
            </div>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition"
              title="Refresh circuits"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>

        {circuitEntries.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No circuit breaker statuses registered.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {circuitEntries.map(([name, cb]) => {
              const isOpen = cb.state === "open";
              const isHalfOpen = cb.state === "half_open";

              return (
                <div
                  key={name}
                  className={`p-4 rounded-lg border transition-all ${
                    isOpen
                      ? "bg-red-950/20 border-red-800/50"
                      : isHalfOpen
                      ? "bg-amber-950/20 border-amber-800/50"
                      : "bg-slate-950/50 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-semibold text-white tracking-wide">
                      {cb.component || name}
                    </span>
                    {getCircuitBadge(cb.state)}
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/60 font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Failures / Threshold:</span>
                      <span className={cb.failure_count > 0 ? "text-amber-400" : "text-slate-300"}>
                        {cb.failure_count} / {cb.failure_threshold}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Window / Duration:</span>
                      <span className="text-slate-300">
                        {cb.window_seconds}s / {cb.open_duration_seconds}s
                      </span>
                    </div>
                    {cb.last_failure_at && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Last Tripped:</span>
                        <span className="text-red-400">
                          {new Date(cb.last_failure_at).toLocaleTimeString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bulkhead Isolation Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-semibold text-white">Subsystem Bulkheads & Concurrency Isolation</h3>
              <p className="text-xs text-slate-400">
                Guaranteed capacity fences to prevent worker exhaustion across execution domains
              </p>
            </div>
          </div>
        </div>

        {bulkheadEntries.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No active bulkhead definitions found.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {bulkheadEntries.map(([subsystem, metrics]) => {
              const max = metrics.max_concurrency || 1;
              const active = metrics.active_slots || 0;
              const available = metrics.available_slots ?? (max - active);
              const pct = Math.round((active / max) * 100);
              const isHigh = pct >= 80;

              return (
                <div
                  key={subsystem}
                  className="p-4 rounded-lg bg-slate-950/50 border border-slate-800 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold text-white capitalize">
                      {subsystem.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`text-xs font-mono font-bold ${
                        isHigh ? "text-amber-400" : "text-emerald-400"
                      }`}
                    >
                      {active} / {max} slots
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-slate-800 rounded-full h-2 my-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isHigh ? "bg-amber-500" : "bg-indigo-500"
                      }`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-[11px] font-mono text-slate-500 mt-2">
                    <span>{pct}% utilized</span>
                    <span>{available} available</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

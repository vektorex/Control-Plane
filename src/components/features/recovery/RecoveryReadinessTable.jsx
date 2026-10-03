"use client";

import React from "react";
import {
  LifeBuoy,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Clock,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

export function RecoveryReadinessTable({ readiness = [], onRefresh }) {
  const getReadinessBadge = (st) => {
    switch (st) {
      case "ready":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3 h-3" /> Ready
          </span>
        );
      case "needs_attention":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
            <AlertTriangle className="w-3 h-3" /> Attention
          </span>
        );
      case "blocked":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
            <XCircle className="w-3 h-3" /> Blocked
          </span>
        );
      default:
        return (
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            {st || "Unknown"}
          </span>
        );
    }
  };

  const formatSeconds = (sec) => {
    if (sec == null) return "-";
    if (sec < 60) return `${sec}s`;
    if (sec < 3600) return `${Math.round(sec / 60)}m`;
    return `${(sec / 3600).toFixed(1)}h`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LifeBuoy className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">
            Operational Recovery Readiness Matrix
          </h3>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            title="Refresh readiness"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Subsystem Resource</th>
              <th className="py-3 px-4 font-semibold">Backup Freshness</th>
              <th className="py-3 px-4 font-semibold">Integrity Verified</th>
              <th className="py-3 px-4 font-semibold">Restore Simulation</th>
              <th className="py-3 px-4 font-semibold">Observed Backup Age</th>
              <th className="py-3 px-4 font-semibold">Blockers</th>
              <th className="py-3 px-4 font-semibold text-right">Readiness State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
            {readiness.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                  No readiness evaluations available. Configure recovery objectives and run a backup.
                </td>
              </tr>
            ) : (
              readiness.map((r) => (
                <tr key={r.resource_type} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-sans font-semibold text-white capitalize">
                    {r.resource_type.replace(/_/g, " ")}
                  </td>
                  <td className="py-3 px-4 font-sans">
                    {r.backup_status === "ready" ? (
                      <span className="text-emerald-400">Available</span>
                    ) : (
                      <span className="text-red-400">Missing</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-sans">
                    {r.verification_status === "verified" ? (
                      <span className="text-emerald-400">Verified</span>
                    ) : (
                      <span className="text-amber-400">Unverified</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-sans">
                    {r.restore_test_status === "passed" ? (
                      <span className="text-emerald-400">Passed</span>
                    ) : (
                      <span className="text-slate-500">Not Tested</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {formatSeconds(r.observed_backup_age_seconds)}
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-sans">
                    {r.known_blockers && r.known_blockers.length > 0 ? (
                      <span className="text-amber-400 font-medium">
                        {r.known_blockers[0]}
                      </span>
                    ) : (
                      <span className="text-slate-600">None</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right font-sans">
                    {getReadinessBadge(r.overall_status)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="p-3 bg-slate-950/40 border-t border-slate-800 text-[11px] text-slate-500 font-sans">
        Factual operational status based on empirical snapshot timestamps and dry-run tests. Does not constitute a contractual SLA guarantee.
      </div>
    </div>
  );
}

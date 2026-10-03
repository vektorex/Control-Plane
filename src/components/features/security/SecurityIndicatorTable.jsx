"use client";

import React, { useState } from "react";
import {
  Activity,
  Clock,
  Filter,
  Shield,
  Key,
  Globe,
  Terminal,
} from "lucide-react";

export function SecurityIndicatorTable({ indicators = [] }) {
  const [filterType, setFilterType] = useState("all");

  const filtered = indicators.filter((ind) => {
    if (filterType !== "all" && ind.indicator_type !== filterType) return false;
    return true;
  });

  const getIndicatorIcon = (type) => {
    switch (type) {
      case "actor_fingerprint":
      case "session_fingerprint":
        return <Key className="w-3.5 h-3.5 text-amber-400" />;
      case "request_fingerprint":
      case "webhook_fingerprint":
        return <Globe className="w-3.5 h-3.5 text-blue-400" />;
      default:
        return <Terminal className="w-3.5 h-3.5 text-indigo-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">Filter Type:</span>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Indicator Types</option>
            <option value="request_fingerprint">Request Fingerprint</option>
            <option value="session_fingerprint">Session Fingerprint</option>
            <option value="actor_fingerprint">Actor Fingerprint</option>
            <option value="artifact_fingerprint">Artifact Fingerprint</option>
            <option value="webhook_fingerprint">Webhook Fingerprint</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Showing {filtered.length} of {indicators.length} indicators (no plaintext secrets stored)
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Type</th>
              <th className="py-3 px-4 font-semibold">Value / Label</th>
              <th className="py-3 px-4 font-semibold">SHA-256 Fingerprint</th>
              <th className="py-3 px-4 font-semibold">Source</th>
              <th className="py-3 px-4 font-semibold">Confidence</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Last Seen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
                  No active threat indicators found.
                </td>
              </tr>
            ) : (
              filtered.map((ind) => (
                <tr key={ind.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5 text-xs font-mono text-slate-200">
                      {getIndicatorIcon(ind.indicator_type)}
                      <span>{ind.indicator_type}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-medium text-white">{ind.value_display}</span>
                  </td>
                  <td className="py-3 px-4">
                    <code className="text-[11px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 font-mono">
                      {ind.value_hash ? ind.value_hash.substring(0, 16) + "..." : "-"}
                    </code>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs text-slate-400">{ind.source}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-mono text-slate-300">
                      {Math.round(ind.confidence * 100)}%
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 font-medium">
                      {ind.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(ind.last_seen_at).toLocaleTimeString()}</span>
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

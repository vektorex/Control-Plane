"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function DecisionLogTable({ decisions = [], loading = false }) {
  const [expandedId, setExpandedId] = useState(null);
  const [filterDecision, setFilterDecision] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-14 rounded-xl bg-slate-900/40 border border-slate-800/60 animate-pulse" />
        ))}
      </div>
    );
  }

  const filtered = decisions.filter((d) => {
    if (filterDecision !== "all" && d.decision !== filterDecision) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const reasonsStr = (d.reasons || []).join(" ").toLowerCase();
      const pointStr = (d.enforcement_point || "").toLowerCase();
      return reasonsStr.includes(term) || pointStr.includes(term);
    }
    return true;
  });

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-4">
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search reasons or points..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 text-xs"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-[11px] text-slate-400">Filter Decision:</span>
          <select
            value={filterDecision}
            onChange={(e) => setFilterDecision(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs"
          >
            <option value="all">All Decisions</option>
            <option value="allow">Allow</option>
            <option value="allow_with_constraints">Allow With Constraints</option>
            <option value="require_approval">Require Approval</option>
            <option value="deny">Deny</option>
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-10 rounded-xl border border-dashed border-slate-800 text-slate-400 text-xs">
          No matching governance decisions recorded in this window.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800/80 bg-slate-950/40">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/70 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Enforcement Point</th>
                  <th className="px-4 py-3">Decision</th>
                  <th className="px-4 py-3">Evaluation Reasons</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {filtered.map((d) => {
                  const isExpanded = expandedId === d.id;
                  const dateStr = d.created_at
                    ? new Date(d.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
                    : "now";

                  return (
                    <React.Fragment key={d.id}>
                      <tr
                        className="hover:bg-slate-900/50 transition-colors cursor-pointer"
                        onClick={() => toggleExpand(d.id)}
                      >
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                          {dateStr}
                        </td>

                        <td className="px-4 py-3 font-mono text-[11px] text-slate-200">
                          {d.enforcement_point}
                        </td>

                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border",
                              d.decision === "allow"
                                ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/40"
                                : d.decision === "allow_with_constraints"
                                ? "bg-cyan-950/40 text-cyan-300 border-cyan-800/40"
                                : d.decision === "require_approval"
                                ? "bg-amber-950/40 text-amber-300 border-amber-800/40"
                                : "bg-rose-950/40 text-rose-300 border-rose-800/40"
                            )}
                          >
                            {d.decision}
                          </span>
                        </td>

                        <td className="px-4 py-3 text-slate-300 truncate max-w-xs text-[11px]">
                          {(d.reasons || []).join(", ") || "Default allow"}
                        </td>

                        <td className="px-4 py-3 font-mono text-[11px] text-slate-400">
                          {d.evaluation_duration_ms ? `${d.evaluation_duration_ms}ms` : "<1ms"}
                        </td>

                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="p-1 rounded text-slate-400 hover:text-white"
                          >
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-slate-900/80">
                          <td colSpan={6} className="p-4 space-y-3">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                              <div>
                                <span className="text-[10px] font-semibold uppercase text-slate-400">
                                  Evaluation Reasons
                                </span>
                                <ul className="mt-1 space-y-1">
                                  {(d.reasons || []).map((r, i) => (
                                    <li key={i} className="text-xs text-slate-200">
                                      • {r}
                                    </li>
                                  ))}
                                </ul>
                              </div>

                              <div>
                                <span className="text-[10px] font-semibold uppercase text-slate-400">
                                  Matched Policy IDs
                                </span>
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {(d.matched_policies || []).map((p, i) => (
                                    <span
                                      key={i}
                                      className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-slate-950 text-indigo-300 border border-slate-800"
                                    >
                                      {p}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>

                            {d.constraints && Object.keys(d.constraints).length > 0 && (
                              <div>
                                <span className="text-[10px] font-semibold uppercase text-slate-400">
                                  Enforced Constraints
                                </span>
                                <pre className="mt-1 p-2 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-cyan-300 overflow-x-auto">
                                  {JSON.stringify(d.constraints, null, 2)}
                                </pre>
                              </div>
                            )}

                            {d.sanitized_context && Object.keys(d.sanitized_context).length > 0 && (
                              <div>
                                <span className="text-[10px] font-semibold uppercase text-slate-400">
                                  Sanitized Context Snapshot
                                </span>
                                <pre className="mt-1 p-2 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-400 overflow-x-auto">
                                  {JSON.stringify(d.sanitized_context, null, 2)}
                                </pre>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

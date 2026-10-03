"use client";

import React from "react";
import {
  Shield,
  Layers,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Play,
  Edit2,
  Trash2,
  ChevronRight,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";

const scopeColors = {
  system: "bg-purple-950/60 text-purple-300 border-purple-800/40",
  organization: "bg-indigo-950/60 text-indigo-300 border-indigo-800/40",
  workspace: "bg-emerald-950/60 text-emerald-300 border-emerald-800/40",
  project: "bg-amber-950/60 text-amber-300 border-amber-800/40",
};

export function PolicyListTable({
  policies = [],
  loading = false,
  onSelectPolicy,
  onSimulatePolicy,
  onCreateVersion,
  onDeletePolicy,
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 rounded-xl bg-slate-900/40 border border-slate-800/60 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!policies || policies.length === 0) {
    return (
      <div className="text-center py-12 px-4 rounded-xl border border-dashed border-slate-800 bg-slate-900/20">
        <Shield className="w-10 h-10 text-slate-400 mx-auto mb-3" />
        <h3 className="text-sm font-medium text-slate-200">No governance policies defined</h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
          Create organizational guardrails for model access, destructive tool calls, sensitive data, and cost caps.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800/80 bg-slate-950/40 shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/70 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3">Policy Name & Scope</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Active Version</th>
              <th className="px-4 py-3">Rules</th>
              <th className="px-4 py-3">Fail-Safe</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {policies.map((p) => {
              const activeVer = p.active_version;
              const ruleCount = activeVer?.rules?.length || 0;
              const isFailClosed = p.fail_safe_mode === "fail_closed";

              return (
                <tr
                  key={p.id}
                  className="hover:bg-slate-900/50 transition-colors group cursor-pointer"
                  onClick={() => onSelectPolicy && onSelectPolicy(p)}
                >
                  <td className="px-4 py-3.5">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors">
                          {p.name}
                        </span>
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-[10px] font-mono border capitalize",
                            scopeColors[p.scope] || "bg-slate-800 text-slate-300 border-slate-700"
                          )}
                        >
                          {p.scope}
                        </span>
                      </div>
                      {p.description && (
                        <span className="text-[11px] text-slate-400 truncate max-w-xs mt-0.5">
                          {p.description}
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="px-4 py-3.5 text-slate-300 capitalize font-mono text-[11px]">
                    {p.policy_type || "general"}
                  </td>

                  <td className="px-4 py-3.5">
                    {activeVer ? (
                      <div className="flex items-center gap-1.5">
                        <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-slate-800/80 text-slate-200 border border-slate-700/60">
                          v{activeVer.version_number}
                        </span>
                        <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          active
                        </span>
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">No active version</span>
                    )}
                  </td>

                  <td className="px-4 py-3.5 font-mono text-[11px] text-slate-300">
                    {ruleCount} {ruleCount === 1 ? "rule" : "rules"}
                  </td>

                  <td className="px-4 py-3.5">
                    <span
                      className={cn(
                        "px-1.5 py-0.5 rounded text-[10px] font-mono border",
                        isFailClosed
                          ? "bg-rose-950/40 text-rose-300 border-rose-800/40"
                          : "bg-slate-800/60 text-slate-400 border-slate-700/40"
                      )}
                    >
                      {p.fail_safe_mode || "fail_closed"}
                    </span>
                  </td>

                  <td className="px-4 py-3.5">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border",
                        p.status === "active"
                          ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/40"
                          : p.status === "draft"
                          ? "bg-amber-950/40 text-amber-300 border-amber-800/40"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      )}
                    >
                      <span
                        className={cn(
                          "w-1.5 h-1.5 rounded-full",
                          p.status === "active" ? "bg-emerald-400" : "bg-amber-400"
                        )}
                      />
                      {p.status}
                    </span>
                  </td>

                  <td className="px-4 py-3.5 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        title="Simulate Policy"
                        onClick={() => onSimulatePolicy && onSimulatePolicy(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-slate-800/80 transition-colors"
                      >
                        <Play className="w-3.5 h-3.5" />
                      </button>
                      <button
                        title="New Version"
                        onClick={() => onCreateVersion && onCreateVersion(p)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-300 hover:bg-slate-800/80 transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                      <button
                        title="Archive Policy"
                        onClick={() => onDeletePolicy && onDeletePolicy(p.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

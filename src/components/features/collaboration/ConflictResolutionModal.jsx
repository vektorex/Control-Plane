"use client";

import React from "react";
import { AlertTriangle, RefreshCw, X } from "lucide-react";

export function ConflictResolutionModal({
  conflict,
  onResolve,
  onCancel,
}) {
  if (!conflict) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="flex flex-col gap-4 w-full max-w-lg p-5 rounded-2xl bg-slate-900 border border-amber-500/30 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-amber-400">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="font-semibold text-sm text-slate-100">Optimistic Concurrency Conflict (409)</h3>
          </div>
          <button onClick={onCancel} className="text-slate-500 hover:text-slate-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          Another collaborator modified this resource concurrently. Your edit was based on version{" "}
          <span className="font-mono font-bold text-amber-400">{conflict.expected_version}</span>, but the authoritative
          server version is now <span className="font-mono font-bold text-emerald-400">{conflict.current_version}</span>.
        </p>

        <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-400 flex flex-col gap-1">
          <div><span className="text-slate-500">Resource:</span> {conflict.resource_id}</div>
          <div><span className="text-slate-500">Current Server Version:</span> v{conflict.current_version}</div>
          <div><span className="text-slate-500">Your Base Version:</span> v{conflict.expected_version}</div>
        </div>

        <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-[11px] text-amber-300">
          <span className="font-semibold">Merge Safety Rule:</span> Governance policies, security rules, and published
          versions cannot be automatically merged. Safe metadata may be reconciled manually.
        </div>

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
          <button
            onClick={() => onResolve("keep_current")}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Discard My Changes & Reload
          </button>
          <button
            onClick={() => onResolve("apply_changes")}
            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-colors"
          >
            Overwrite With Mine (Force)
          </button>
        </div>
      </div>
    </div>
  );
}

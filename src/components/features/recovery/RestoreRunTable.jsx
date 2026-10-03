"use client";

import React from "react";
import Link from "next/link";
import {
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
} from "lucide-react";

export function RestoreRunTable({ restores = [], onRefresh }) {
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
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
            <XCircle className="w-3 h-3" /> Failed
          </span>
        );
      default:
        return (
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
            {st}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <RotateCcw className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">Restore Execution History</h3>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {restores.length} executions recorded
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Execution ID</th>
              <th className="py-3 px-4 font-semibold">Plan ID</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Restored</th>
              <th className="py-3 px-4 font-semibold">Skipped / Failed</th>
              <th className="py-3 px-4 font-semibold">Started At</th>
              <th className="py-3 px-4 font-semibold text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
            {restores.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                  No restore execution runs recorded yet.
                </td>
              </tr>
            ) : (
              restores.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-semibold text-white">
                    {r.id.slice(0, 13)}...
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {r.restore_plan_id.slice(0, 13)}...
                  </td>
                  <td className="py-3 px-4 font-sans">{getStatusBadge(r.status)}</td>
                  <td className="py-3 px-4 text-emerald-400 font-bold">
                    {r.restored_count} / {r.resource_count}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    <span>{r.skipped_count}</span>
                    <span className="text-slate-600"> / </span>
                    <span className={r.failed_count > 0 ? "text-red-400 font-bold" : "text-slate-500"}>
                      {r.failed_count}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-sans">
                    {new Date(r.started_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-sans">
                    <Link
                      href={`/app/recovery/restores/${r.id}`}
                      className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium text-xs"
                    >
                      Inspect <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
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

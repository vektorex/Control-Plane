"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { recoveryService } from "@/services/recovery";

export default function RestoreDetailPage({ params }) {
  const unwrappedParams = use(params);
  const restoreId = unwrappedParams.restoreId;

  const [restore, setRestore] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.getRestore(restoreId);
      setRestore(res);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load restore execution details.");
    } finally {
      setIsLoading(false);
    }
  }, [restoreId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading && !restore) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
        Loading restore execution...
      </div>
    );
  }

  if (errorMsg || !restore) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/app/recovery/restores"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Restores
        </Link>
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-200 text-sm">
          {errorMsg || "Restore execution not found."}
        </div>
      </div>
    );
  }

  const logEntries = restore.execution_log || [];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <Link
          href="/app/recovery/restores"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Restores
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl">
              <RotateCcw className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight font-mono">
                  {restore.id}
                </h1>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                  {restore.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Plan ID: {restore.restore_plan_id} • Started: {new Date(restore.started_at).toLocaleString()}
              </p>
            </div>
          </div>

          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono">
          <span className="text-xs text-slate-400 uppercase font-sans font-semibold">Status</span>
          <div className="mt-2 text-sm font-bold text-white uppercase">
            {restore.status}
          </div>
          <span className="text-[11px] text-slate-500 font-sans mt-1 block">
            {restore.completed_at ? "Finished" : "Running"}
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono">
          <span className="text-xs text-slate-400 uppercase font-sans font-semibold">Restored</span>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            {restore.restored_count}
          </div>
          <span className="text-[11px] text-slate-500 font-sans mt-1 block">
            / {restore.resource_count} total resources
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono">
          <span className="text-xs text-slate-400 uppercase font-sans font-semibold">Skipped</span>
          <div className="mt-2 text-2xl font-bold text-slate-300">
            {restore.skipped_count}
          </div>
          <span className="text-[11px] text-slate-500 font-sans mt-1 block">
            Conflicts preserved
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono">
          <span className="text-xs text-slate-400 uppercase font-sans font-semibold">Failed</span>
          <div className={`mt-2 text-2xl font-bold ${restore.failed_count > 0 ? "text-red-400" : "text-slate-500"}`}>
            {restore.failed_count}
          </div>
          <span className="text-[11px] text-slate-500 font-sans mt-1 block">
            Errors encountered
          </span>
        </div>
      </div>

      {restore.error && (
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-200 text-xs font-mono">
          <span className="font-bold block mb-1">Execution Failure:</span>
          {restore.error}
        </div>
      )}

      {/* Execution Log */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Execution Stream</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">{logEntries.length} log events</span>
        </div>

        {logEntries.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">
            No execution stream entries captured.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {logEntries.map((entry, idx) => (
              <div key={idx} className="p-3 flex items-center justify-between hover:bg-slate-800/20">
                <div className="space-y-0.5">
                  <div className="text-white font-semibold">
                    [{entry.resource_type}] {entry.resource_id}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Action: {entry.action} • {entry.secret_handling}
                  </div>
                </div>
                <div className="text-slate-500 text-[11px]">
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : "-"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

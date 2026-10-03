"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Archive,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  RefreshCw,
  RotateCcw,
  Trash2,
} from "lucide-react";

export function BackupTable({
  backups = [],
  onVerify,
  onDryRun,
  onExpire,
  onRefresh,
}) {
  const [filterStatus, setFilterStatus] = useState("all");

  const filtered = backups.filter((b) => {
    if (filterStatus !== "all" && b.status !== filterStatus) return false;
    return true;
  });

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
      case "verifying":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
            <ShieldCheck className="w-3 h-3" /> Verifying
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
            <XCircle className="w-3 h-3" /> Failed
          </span>
        );
      case "expired":
        return (
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-500 font-medium">
            Expired
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

  const getClassificationBadge = (cls) => {
    switch (cls) {
      case "restricted":
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-red-950/80 text-red-300 border border-red-800">
            Restricted
          </span>
        );
      case "confidential":
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800">
            Confidential
          </span>
        );
      case "internal":
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800">
            Internal
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            Public
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">Filter By Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="running">Running</option>
            <option value="failed">Failed</option>
            <option value="expired">Expired</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Showing {filtered.length} of {backups.length} snapshots
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Snapshot ID</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Classification</th>
              <th className="py-3 px-4 font-semibold">Resources</th>
              <th className="py-3 px-4 font-semibold">Verification</th>
              <th className="py-3 px-4 font-semibold">Created At</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
                  No backup snapshots match the filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((b) => {
                const isVerified = b.manifest?.verification_status === "verified";
                const isExpired = b.status === "expired";

                return (
                  <tr key={b.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono text-xs">
                      <div className="font-semibold text-white">
                        {b.id.slice(0, 13)}...
                      </div>
                      <div className="text-[11px] text-slate-500">v{b.backup_version}</div>
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(b.status)}</td>
                    <td className="py-3 px-4">{getClassificationBadge(b.classification)}</td>
                    <td className="py-3 px-4 font-mono text-xs">
                      <span className="text-white font-semibold">{b.resource_count}</span>
                      <span className="text-slate-500"> assets</span>
                    </td>
                    <td className="py-3 px-4">
                      {isVerified ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                          <CheckCircle2 className="w-3 h-3" /> Verified
                        </span>
                      ) : b.status === "completed" ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                          <AlertTriangle className="w-3 h-3" /> Unverified
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-400">
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {b.status === "completed" && !isVerified && onVerify && (
                          <button
                            onClick={() => onVerify(b.id)}
                            className="p-1 rounded hover:bg-slate-800 text-indigo-400 hover:text-indigo-300 text-xs font-medium"
                            title="Verify Integrity"
                          >
                            Verify
                          </button>
                        )}

                        {b.status === "completed" && onDryRun && (
                          <button
                            onClick={() => onDryRun(b)}
                            className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-medium"
                            title="Dry-Run Restore"
                          >
                            Dry-Run
                          </button>
                        )}

                        {!isExpired && onExpire && (
                          <button
                            onClick={() => onExpire(b.id)}
                            className="p-1 rounded hover:bg-slate-800 text-red-400 hover:text-red-300 text-xs font-medium"
                            title="Expire Backup"
                          >
                            Expire
                          </button>
                        )}

                        <Link
                          href={`/app/recovery/backups/${b.id}`}
                          className="p-1 text-slate-400 hover:text-white inline-flex items-center gap-1 text-xs"
                        >
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

"use client";

import React from "react";
import {
  Database,
  ShieldAlert,
  Lock,
  FileCheck2,
  AlertOctagon,
  KeyRound,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export function DataGovernanceStatsCards({ overview, loading = false }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-xl bg-slate-900/60 border border-slate-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  const o = overview || {};
  const totalAssets = o.total_assets ?? 0;
  const activeHolds = o.active_legal_holds ?? 0;
  const pendingDeletions = o.pending_deletions ?? 0;
  const pendingPrivacy = o.pending_privacy_requests ?? 0;
  const recentEvidence = o.recent_evidence_count ?? 0;
  const assetsWithFindings = o.assets_with_findings ?? 0;
  const chainValid = o.evidence_chain_valid ?? true;
  const classCounts = o.classification_counts || {};

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Data Assets */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Tracked Data Assets</span>
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <Database className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white">{totalAssets}</span>
          <span className="text-xs text-slate-400">across tenant</span>
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-400 overflow-hidden">
          <span className="text-emerald-400">{classCounts.public || 0} pub</span>
          <span>•</span>
          <span className="text-blue-400">{classCounts.internal || 0} int</span>
          <span>•</span>
          <span className="text-amber-400">{classCounts.confidential || 0} conf</span>
          <span>•</span>
          <span className="text-rose-400">{classCounts.restricted || 0} rest</span>
        </div>
      </div>

      {/* Cryptographic Evidence Chain */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Evidence Chain Status</span>
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center border ${
              chainValid
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-rose-500/10 text-rose-400 border-rose-500/20"
            }`}
          >
            <FileCheck2 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span
            className={`text-2xl font-bold tracking-tight ${
              chainValid ? "text-emerald-300" : "text-rose-400"
            }`}
          >
            {chainValid ? "Intact" : "Tampered"}
          </span>
          <span className="text-xs text-slate-400 font-mono">
            {recentEvidence} logs
          </span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400 flex items-center gap-1">
          {chainValid ? (
            <>
              <CheckCircle2 className="w-3 h-3 text-emerald-400 inline" />
              <span>SHA-256 Hash chained</span>
            </>
          ) : (
            <>
              <XCircle className="w-3 h-3 text-rose-400 inline" />
              <span className="text-rose-400 font-semibold">Integrity mismatch</span>
            </>
          )}
        </p>
      </div>

      {/* Active Legal Holds */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Active Legal Holds</span>
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
            <Lock className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-amber-300">
            {activeHolds}
          </span>
          <span className="text-xs text-amber-400/80">holds active</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">
          Strictly prevents deletion of bound assets
        </p>
      </div>

      {/* Privacy & Lifecycle Queue */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Pending Actions</span>
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400 border border-sky-500/20">
            <AlertOctagon className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white">
            {pendingDeletions + pendingPrivacy}
          </span>
          <span className="text-xs text-slate-400">
            ({pendingDeletions} del / {pendingPrivacy} req)
          </span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">
          {assetsWithFindings} assets with PII / secrets
        </p>
      </div>
    </div>
  );
}

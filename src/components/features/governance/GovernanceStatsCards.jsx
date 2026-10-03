"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, AlertTriangle, Coins, Lock, CheckCircle2 } from "lucide-react";

export function GovernanceStatsCards({ stats, loading = false }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900/60 border border-slate-800 animate-pulse" />
        ))}
      </div>
    );
  }

  const s = stats || {};
  const activeCount = s.active_policies_count ?? 0;
  const totalDecisions = s.total_decisions_count ?? 0;
  const blocksCount = s.denied_decisions_count ?? 0;
  const approvalsCount = s.approvals_required_count ?? 0;
  const budgetPolicy = s.budget_policy || null;

  const blockRate = totalDecisions > 0 ? ((blocksCount / totalDecisions) * 100).toFixed(1) : "0.0";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Active Policies */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Active Policies</span>
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <ShieldCheck className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white">{activeCount}</span>
          <span className="text-xs text-slate-400">in scope</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">System, Org & Workspace rules</p>
      </div>

      {/* Enforcements & Blocks */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Policy Blocks</span>
          <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center text-rose-400 border border-rose-500/20">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-rose-300">{blocksCount}</span>
          <span className="text-xs text-rose-400/80 font-mono">({blockRate}%)</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">Blocked operations / {totalDecisions} total</p>
      </div>

      {/* Approvals Required */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Approvals Gated</span>
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-amber-300">{approvalsCount}</span>
          <span className="text-xs text-slate-400">HITL gates</span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">Sensitive / privileged actions</p>
      </div>

      {/* Budget Caps */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm shadow-sm hover:border-slate-700/80 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">Budget Guardrails</span>
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <Coins className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-white">
            {budgetPolicy?.max_cost_per_period ? `$${budgetPolicy.max_cost_per_period.toFixed(2)}` : "Active"}
          </span>
          <span className="text-xs text-emerald-400 font-mono">
            {budgetPolicy?.period || "monthly"}
          </span>
        </div>
        <p className="mt-1 text-[11px] text-slate-400">
          Hard Cap: {budgetPolicy?.hard_limit_action || "deny"}
        </p>
      </div>
    </div>
  );
}

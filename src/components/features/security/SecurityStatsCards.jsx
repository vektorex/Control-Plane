"use client";

import React from "react";
import {
  AlertTriangle,
  ShieldAlert,
  Flame,
  Activity,
  CheckCircle2,
  Lock,
  Workflow,
  Database,
  Cpu,
} from "lucide-react";

export function SecurityStatsCards({ overview, statistics }) {
  const openIncidents = overview?.open_incidents ?? 0;
  const criticalSignals = overview?.critical_signals ?? 0;
  const highSignals = overview?.high_signals ?? 0;
  const activeIndicators = overview?.active_indicators ?? 0;
  const pendingContainments = overview?.pending_containments ?? 0;
  const byCategory = overview?.incidents_by_category ?? {};
  const signalsByType = statistics?.signals_by_type ?? {};

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Open Incidents */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Open Incidents
            </span>
            <div className="p-2 rounded-lg bg-red-950/60 border border-red-800/40 text-red-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">
              {openIncidents}
            </span>
            <span className="text-xs text-slate-500">active triage</span>
          </div>
        </div>

        {/* Critical & High Signals */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Critical & High Signals
            </span>
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-800/40 text-amber-400">
              <Flame className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-400 tracking-tight">
              {criticalSignals + highSignals}
            </span>
            <span className="text-xs text-slate-500">
              ({criticalSignals} crit, {highSignals} high)
            </span>
          </div>
        </div>

        {/* Pending Containment */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Pending Containment
            </span>
            <div className="p-2 rounded-lg bg-orange-950/60 border border-orange-800/40 text-orange-400">
              <Lock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-orange-400 tracking-tight">
              {pendingContainments}
            </span>
            <span className="text-xs text-slate-500">awaiting HITL/exec</span>
          </div>
        </div>

        {/* Threat Indicators */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Active Indicators
            </span>
            <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-800/40 text-blue-400">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tracking-tight">
              {activeIndicators}
            </span>
            <span className="text-xs text-slate-500">fingerprints tracked</span>
          </div>
        </div>

        {/* Playbooks Active */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Active Playbooks
            </span>
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800/40 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-emerald-400 tracking-tight">
              {overview?.active_playbooks ?? 0}
            </span>
            <span className="text-xs text-slate-500">automated rules</span>
          </div>
        </div>
      </div>

      {/* Domain Breakdown Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2 bg-slate-950/50 p-3 rounded-lg border border-slate-800/60 text-xs">
        <div className="flex items-center gap-1.5 text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span>Injection:</span>
          <strong className="text-white font-semibold">
            {signalsByType["prompt_injection"] || 0}
          </strong>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <Database className="w-3.5 h-3.5 text-rose-400" />
          <span>Data Exposure:</span>
          <strong className="text-white font-semibold">
            {(signalsByType["secret_detection"] || 0) + (signalsByType["pii_exposure"] || 0)}
          </strong>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <Lock className="w-3.5 h-3.5 text-amber-400" />
          <span>Auth/RBAC:</span>
          <strong className="text-white font-semibold">
            {(signalsByType["authorization_denied"] || 0) + (signalsByType["authentication_failure"] || 0)}
          </strong>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <Workflow className="w-3.5 h-3.5 text-purple-400" />
          <span>Workflow/Job:</span>
          <strong className="text-white font-semibold">
            {signalsByType["suspicious_workflow"] || 0}
          </strong>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <AlertTriangle className="w-3.5 h-3.5 text-cyan-400" />
          <span>Tool/Connector:</span>
          <strong className="text-white font-semibold">
            {(signalsByType["tool_abuse"] || 0) + (signalsByType["connector_abuse"] || 0)}
          </strong>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span>Tenant Boundary:</span>
          <strong className="text-white font-semibold">
            {signalsByType["tenant_isolation_violation"] || 0}
          </strong>
        </div>
      </div>
    </div>
  );
}

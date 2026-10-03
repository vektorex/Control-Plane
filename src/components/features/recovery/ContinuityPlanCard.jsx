"use client";

import React from "react";
import {
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  PhoneCall,
} from "lucide-react";

export function ContinuityPlanCard({ plan }) {
  if (!plan) return null;

  const recoveryOrder = plan.recovery_order || [];
  const criticalServices = plan.critical_services || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            {plan.name}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {plan.description || "Documented business continuity plan"}
          </p>
        </div>
        <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-medium">
          Active Plan
        </span>
      </div>

      {/* Critical Services List */}
      <div className="space-y-1.5">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">
          Critical Services ({criticalServices.length})
        </span>
        <div className="flex flex-wrap gap-1.5">
          {criticalServices.map((svc) => (
            <span
              key={svc}
              className="text-xs font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 capitalize"
            >
              {svc.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      </div>

      {/* Recovery Sequence */}
      <div className="space-y-2 pt-2 border-t border-slate-800/80">
        <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">
          Ordered Recovery Sequence
        </span>
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          {recoveryOrder.map((step, idx) => (
            <React.Fragment key={step}>
              <span className="px-2 py-1 rounded bg-slate-800 text-indigo-300 font-medium capitalize">
                {idx + 1}. {step.replace(/_/g, " ")}
              </span>
              {idx < recoveryOrder.length - 1 && (
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center justify-between font-mono">
        <span>Owner: {plan.owner_id}</span>
        <span>Updated: {new Date(plan.updated_at).toLocaleDateString()}</span>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  Target,
  PieChart,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  ShieldCheck,
} from "lucide-react";

export function ReliabilityObjectiveTable({
  objectives = [],
  budgets = [],
  onRefresh,
}) {
  const [activeTab, setActiveTab] = useState("objectives");

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-indigo-400" />
            Service Level Objectives & Operational Budgets
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Internal operational targets and error allowances. Does not represent contractual SLA guarantees.
          </p>
        </div>

        <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab("objectives")}
            className={`px-3 py-1 rounded font-medium transition ${
              activeTab === "objectives"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Objectives (SLOs) ({objectives.length})
          </button>
          <button
            onClick={() => setActiveTab("budgets")}
            className={`px-3 py-1 rounded font-medium transition ${
              activeTab === "budgets"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Failure Budgets ({budgets.length})
          </button>
        </div>
      </div>

      {activeTab === "objectives" ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Component</th>
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold">Target Metric</th>
                <th className="py-3 px-4 font-semibold">Target Value</th>
                <th className="py-3 px-4 font-semibold">Measurement Window</th>
                <th className="py-3 px-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {objectives.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No reliability objectives defined. Add SLO thresholds via Step 32 Governance policies.
                  </td>
                </tr>
              ) : (
                objectives.map((obj) => (
                  <tr key={obj.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-semibold text-white font-sans">
                      {obj.component_name}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                        {obj.component_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-indigo-300 uppercase">
                      {obj.metric.replace(/_/g, " ")}
                    </td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">
                      {obj.metric === "latency" ? `${obj.target}ms` : `${obj.target}%`}
                    </td>
                    <td className="py-3 px-4 text-slate-400 flex items-center gap-1.5 pt-4">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      {obj.window} rolling
                    </td>
                    <td className="py-3 px-4">
                      {obj.enabled ? (
                        <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded font-sans font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                          <CheckCircle2 className="w-3 h-3" /> Monitored
                        </span>
                      ) : (
                        <span className="text-[11px] px-2 py-0.5 rounded font-sans text-slate-500 bg-slate-800">
                          Disabled
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Component</th>
                <th className="py-3 px-4 font-semibold">Metric</th>
                <th className="py-3 px-4 font-semibold">Window</th>
                <th className="py-3 px-4 font-semibold">Budget Allowance</th>
                <th className="py-3 px-4 font-semibold">Current Consumed</th>
                <th className="py-3 px-4 font-semibold">Budget Burn State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {budgets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    No failure budgets configured.
                  </td>
                </tr>
              ) : (
                budgets.map((b) => {
                  const allowed = b.allowed_failure_amount || 1;
                  const current = b.current_failure_amount || 0;
                  const pctBurned = Math.round((current / allowed) * 100);
                  const isExhausted = pctBurned >= 100;
                  const isWarning = pctBurned >= 75 && !isExhausted;

                  return (
                    <tr key={b.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-semibold text-white font-sans">
                        {b.component}
                      </td>
                      <td className="py-3 px-4 text-indigo-300 uppercase">
                        {b.metric.replace(/_/g, " ")}
                      </td>
                      <td className="py-3 px-4 text-slate-400">{b.window}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {b.allowed_failure_amount} errs
                      </td>
                      <td className="py-3 px-4 text-amber-400 font-bold">
                        {b.current_failure_amount}
                      </td>
                      <td className="py-3 px-4">
                        <div className="w-36">
                          <div className="flex justify-between text-[11px] mb-1">
                            <span
                              className={
                                isExhausted
                                  ? "text-red-400 font-bold"
                                  : isWarning
                                  ? "text-amber-400"
                                  : "text-emerald-400"
                              }
                            >
                              {pctBurned}% burned
                            </span>
                            <span className="text-slate-500 font-sans text-[10px]">
                              {isExhausted ? "DEPLETED" : "RESERVE OK"}
                            </span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-1.5 rounded-full ${
                                isExhausted
                                  ? "bg-red-500"
                                  : isWarning
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(pctBurned, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="p-3 bg-slate-950/40 border-t border-slate-800 text-[11px] text-slate-500 flex items-center gap-1.5">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span>
          Failure budget depletion does not automatically block operational executions unless explicitly commanded by Step 32 Governance policies.
        </span>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { Coins, AlertTriangle, ShieldCheck, Save, Clock } from "lucide-react";
import { governanceService } from "@/services/governance";

export function BudgetPolicyCard({
  budgetPolicy,
  workspaceId,
  onUpdated,
}) {
  const [maxCostRun, setMaxCostRun] = useState(budgetPolicy?.max_cost_per_run ?? 2.0);
  const [maxCostPeriod, setMaxCostPeriod] = useState(budgetPolicy?.max_cost_per_period ?? 50.0);
  const [maxTokensRun, setMaxTokensRun] = useState(budgetPolicy?.max_tokens_per_run ?? 32000);
  const [period, setPeriod] = useState(budgetPolicy?.period ?? "monthly");
  const [hardAction, setHardAction] = useState(budgetPolicy?.hard_limit_action ?? "deny");
  const [softThreshold, setSoftThreshold] = useState(budgetPolicy?.soft_threshold_percent ?? 80);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await governanceService.upsertBudget({
        workspace_id: workspaceId,
        scope: "workspace",
        max_cost_per_run: parseFloat(maxCostRun) || null,
        max_cost_per_period: parseFloat(maxCostPeriod) || null,
        max_tokens_per_run: parseInt(maxTokensRun) || null,
        period: period,
        hard_limit_action: hardAction,
        soft_threshold_percent: parseInt(softThreshold) || 80,
      });
      setMessage({ type: "success", text: "Budget policy updated successfully" });
      if (onUpdated) onUpdated();
    } catch (err) {
      setMessage({ type: "error", text: err?.message || "Failed to update budget policy" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm text-xs text-slate-200">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <Coins className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Spend & Budget Guardrails</h3>
            <p className="text-[11px] text-slate-400">
              Enforce deterministic financial guardrails and token limits across execution pipelines.
            </p>
          </div>
        </div>
      </div>

      {message && (
        <div
          className={`mt-4 p-3 rounded-lg border text-xs ${
            message.type === "success"
              ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
              : "bg-rose-950/40 border-rose-800/60 text-rose-300"
          }`}
        >
          {message.text}
        </div>
      )}

      <form onSubmit={handleSave} className="mt-5 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
              Max Cost Per Run ($)
            </label>
            <input
              type="number"
              step="0.01"
              value={maxCostRun}
              onChange={(e) => setMaxCostRun(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
              Max Cost Per Period ($)
            </label>
            <input
              type="number"
              step="0.10"
              value={maxCostPeriod}
              onChange={(e) => setMaxCostPeriod(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
              Max Tokens Per Run
            </label>
            <input
              type="number"
              value={maxTokensRun}
              onChange={(e) => setMaxTokensRun(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs font-mono"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
              Accounting Period
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
              Hard Cap Action
            </label>
            <select
              value={hardAction}
              onChange={(e) => setHardAction(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 text-xs"
            >
              <option value="deny">Deny Execution (Fail-closed)</option>
              <option value="require_approval">Require HITL Approval</option>
              <option value="notify">Notify Only</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
              Soft Alert Threshold ({softThreshold}%)
            </label>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={softThreshold}
              onChange={(e) => setSoftThreshold(e.target.value)}
              className="w-full mt-2"
            />
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 font-medium text-xs transition-colors disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? "Saving Guardrails..." : "Save Budget Policies"}
          </button>
        </div>
      </form>
    </div>
  );
}

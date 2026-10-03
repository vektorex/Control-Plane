"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Settings, ShieldAlert, RefreshCw, AlertCircle } from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { governanceService } from "@/services/governance";
import { BudgetPolicyCard } from "@/components/features/governance/BudgetPolicyCard";

export default function GovernanceSettingsPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [budgetPolicy, setBudgetPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await governanceService.getBudget({ workspaceId });
      setBudgetPolicy(res);
    } catch (err) {
      setError(err?.message || "Failed to load governance workspace settings");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="space-y-6 p-6 max-w-4xl mx-auto text-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/app/governance"
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Back to Governance Dashboard</span>
            </Link>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <ShieldAlert className="h-5 w-5 text-indigo-400" />
            <span>Workspace Governance & Spend Settings</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Configure default guardrails, hard limit enforcement actions, and budget caps for this workspace.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      <BudgetPolicyCard
        budgetPolicy={budgetPolicy}
        workspaceId={workspaceId}
        onUpdated={loadData}
      />
    </div>
  );
}

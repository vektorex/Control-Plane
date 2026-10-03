"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, RefreshCw, History, ShieldAlert, AlertCircle } from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { governanceService } from "@/services/governance";
import { DecisionLogTable } from "@/components/features/governance/DecisionLogTable";

export default function GovernanceDecisionsPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDecisions = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await governanceService.listDecisions({
        workspaceId,
        limit: 150,
      });
      setDecisions(res || []);
    } catch (err) {
      setError(err?.message || "Failed to load governance decisions");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadDecisions();
  }, [loadDecisions]);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link
            href="/app/governance"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">
                Governance Decision Audit Log
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                Immutable
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Comprehensive compliance records for every policy evaluation across tasks, tools, models, and workflows.
            </p>
          </div>
        </div>

        <button
          onClick={loadDecisions}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      <DecisionLogTable decisions={decisions} loading={loading} />
    </div>
  );
}

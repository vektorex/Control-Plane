"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Plus,
  Play,
  FileText,
  Sliders,
  Coins,
  History,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { governanceService } from "@/services/governance";
import { GovernanceStatsCards } from "@/components/features/governance/GovernanceStatsCards";
import { PolicyListTable } from "@/components/features/governance/PolicyListTable";
import { PolicyFormModal } from "@/components/features/governance/PolicyFormModal";
import { PolicySimulatorModal } from "@/components/features/governance/PolicySimulatorModal";
import { DecisionLogTable } from "@/components/features/governance/DecisionLogTable";
import { BudgetPolicyCard } from "@/components/features/governance/BudgetPolicyCard";

export default function GovernanceDashboardPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [activeTab, setActiveTab] = useState("policies");
  const [stats, setStats] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [budgetPolicy, setBudgetPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [simulatorModalOpen, setSimulatorModalOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState(null);

  const loadData = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const [statsRes, policiesRes, decisionsRes, budgetRes] = await Promise.allSettled([
        governanceService.getStats(workspaceId),
        governanceService.listPolicies({ workspaceId }),
        governanceService.listDecisions({ workspaceId, limit: 50 }),
        governanceService.getBudget({ workspaceId }),
      ]);

      if (statsRes.status === "fulfilled") setStats(statsRes.value);
      if (policiesRes.status === "fulfilled") setPolicies(policiesRes.value || []);
      if (decisionsRes.status === "fulfilled") setDecisions(decisionsRes.value || []);
      if (budgetRes.status === "fulfilled") setBudgetPolicy(budgetRes.value);
    } catch (err) {
      setError(err?.message || "Failed to load governance control plane data");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreatePolicy = async (payload) => {
    await governanceService.createPolicy(payload);
    await loadData();
  };

  const handleDeletePolicy = async (policyId) => {
    if (!confirm("Are you sure you want to archive this governance policy?")) return;
    try {
      await governanceService.deletePolicy(policyId);
      await loadData();
    } catch (err) {
      alert(err?.message || "Failed to archive policy");
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-inner">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">
                  AI Governance & Guardrails
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 uppercase">
                  Control Plane
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Centralized deterministic policy enforcement, safety guardrails, budget caps, and audit trails.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800/80 text-xs font-medium transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          <button
            onClick={() => setSimulatorModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-950/40 text-xs font-medium transition-colors shadow-sm"
          >
            <Play className="w-3.5 h-3.5" />
            Policy Simulator
          </button>

          <button
            onClick={() => {
              setSelectedPolicy(null);
              setFormModalOpen(true);
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 text-xs font-semibold shadow-md shadow-indigo-950/50 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            New Policy
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats Cards */}
      <GovernanceStatsCards stats={stats} loading={loading} />

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-px text-xs font-medium">
        <button
          onClick={() => setActiveTab("policies")}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-all ${
            activeTab === "policies"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          Active Policies ({policies.length})
        </button>

        <button
          onClick={() => setActiveTab("decisions")}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-all ${
            activeTab === "decisions"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Audit Decision Log ({decisions.length})
        </button>

        <button
          onClick={() => setActiveTab("budgets")}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-all ${
            activeTab === "budgets"
              ? "border-indigo-500 text-indigo-300 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Coins className="w-3.5 h-3.5" />
          Spend & Budgets
        </button>

        <Link
          href="/app/governance/decisions"
          className="ml-auto text-xs text-slate-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
        >
          <span>Full Decision Explorer</span>
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      {/* Tab Panels */}
      {activeTab === "policies" && (
        <div className="space-y-4">
          <PolicyListTable
            policies={policies}
            loading={loading}
            onSelectPolicy={(p) => {
              setSelectedPolicy(p);
              setFormModalOpen(true);
            }}
            onSimulatePolicy={(p) => {
              setSelectedPolicy(p);
              setSimulatorModalOpen(true);
            }}
            onDeletePolicy={handleDeletePolicy}
          />
        </div>
      )}

      {activeTab === "decisions" && (
        <div className="space-y-4">
          <DecisionLogTable decisions={decisions} loading={loading} />
        </div>
      )}

      {activeTab === "budgets" && (
        <div className="max-w-4xl space-y-4">
          <BudgetPolicyCard
            budgetPolicy={budgetPolicy}
            workspaceId={workspaceId}
            onUpdated={loadData}
          />
        </div>
      )}

      {/* Modals */}
      <PolicyFormModal
        isOpen={formModalOpen}
        onClose={() => {
          setFormModalOpen(false);
          setSelectedPolicy(null);
        }}
        onSubmit={handleCreatePolicy}
        initialData={selectedPolicy}
        workspaceId={workspaceId}
      />

      <PolicySimulatorModal
        isOpen={simulatorModalOpen}
        onClose={() => {
          setSimulatorModalOpen(false);
          setSelectedPolicy(null);
        }}
        workspaceId={workspaceId}
        policyToSimulate={selectedPolicy}
      />
    </div>
  );
}

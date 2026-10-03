"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Layers, Plus, RefreshCw, X } from "lucide-react";
import { recoveryService } from "@/services/recovery";
import { ContinuityPlanCard } from "@/components/features/recovery/ContinuityPlanCard";

export default function ContinuityPage() {
  const [plans, setPlans] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [servicesInput, setServicesInput] = useState(
    "database, authentication, governance, security, ai_gateway, jobs, events, workflows, notifications"
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.listContinuityPlans();
      setPlans(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load continuity plans.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const services = servicesInput
        .split(",")
        .map((s) => s.trim().toLowerCase())
        .filter(Boolean);

      await recoveryService.createContinuityPlan({
        name,
        description,
        critical_services: services,
      });

      setIsModalOpen(false);
      setName("");
      setDescription("");
      fetchData();
    } catch (err) {
      alert(`Error creating plan: ${err.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link
            href="/app/recovery"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Recovery Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <Layers className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Business Continuity Plans
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Define critical service tiers, topological recovery ordering, fallback mechanisms, and owner contacts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" /> New Continuity Plan
          </button>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-200 text-sm">
          {errorMsg}
        </div>
      )}

      <div className="space-y-4">
        {plans.length === 0 ? (
          <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-500 text-xs">
            No business continuity plans defined. Click &quot;New Continuity Plan&quot; to establish an operational restoration plan.
          </div>
        ) : (
          plans.map((plan) => <ContinuityPlanCard key={plan.id} plan={plan} />)
        )}
      </div>

      {/* Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">Create Continuity Plan</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Plan Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Primary Platform Recovery Plan"
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Operational scope and execution criteria..."
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Critical Services (comma-separated)
                </label>
                <textarea
                  rows={3}
                  value={servicesInput}
                  onChange={(e) => setServicesInput(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 font-mono"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Topological restore ordering will automatically be resolved from dependency graphs.
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-semibold"
                >
                  Save Plan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, FlaskConical, Plus, RefreshCw } from "lucide-react";
import { reliabilityService } from "@/services/reliability";
import { ChaosExperimentTable } from "@/components/features/reliability/ChaosExperimentTable";
import { ChaosExperimentModal } from "@/components/features/reliability/ChaosExperimentModal";

export default function ChaosExperimentsPage() {
  const [experiments, setExperiments] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await reliabilityService.listExperiments({ limit: 100 });
      setExperiments(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load chaos experiments.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApprove = async (id) => {
    try {
      await reliabilityService.approveExperiment(id);
      fetchData();
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleRun = async (id) => {
    try {
      await reliabilityService.runExperiment(id);
      fetchData();
    } catch (err) {
      alert(`Run error: ${err.message}`);
    }
  };

  const handleAbort = async (id) => {
    try {
      await reliabilityService.abortExperiment(id, "Operator aborted from experiments page");
      fetchData();
    } catch (err) {
      alert(`Abort error: ${err.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link
            href="/app/reliability"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Reliability Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Chaos Engineering Experiments
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Controlled resilience experiments in sandbox and test environments. Production experiments strictly require Step 32 Governance + Step 18 HITL.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" /> New Experiment
          </button>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh experiments"
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

      <ChaosExperimentTable
        experiments={experiments}
        onApprove={handleApprove}
        onRun={handleRun}
        onAbort={handleAbort}
        onRefresh={fetchData}
      />

      <ChaosExperimentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
}

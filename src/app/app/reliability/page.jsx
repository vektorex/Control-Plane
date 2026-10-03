"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  ShieldAlert,
  Zap,
  RotateCcw,
  Target,
  FlaskConical,
  RefreshCw,
  Plus,
  ArrowRight,
  Sliders,
  Server,
  AlertTriangle,
} from "lucide-react";
import { reliabilityService } from "@/services/reliability";
import { ReliabilityOverviewCards } from "@/components/features/reliability/ReliabilityOverviewCards";
import { ComponentListTable } from "@/components/features/reliability/ComponentListTable";
import { ExecutionCheckpointTable } from "@/components/features/reliability/ExecutionCheckpointTable";
import { ResumeModal } from "@/components/features/reliability/ResumeModal";
import { ChaosExperimentTable } from "@/components/features/reliability/ChaosExperimentTable";
import { ChaosExperimentModal } from "@/components/features/reliability/ChaosExperimentModal";
import { CircuitBreakerPanel } from "@/components/features/reliability/CircuitBreakerPanel";
import { ReliabilityObjectiveTable } from "@/components/features/reliability/ReliabilityObjectiveTable";

export default function ReliabilityDashboardPage() {
  const [activeTab, setActiveTab] = useState("components");
  const [overview, setOverview] = useState(null);
  const [components, setComponents] = useState([]);
  const [checkpoints, setCheckpoints] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [objectives, setObjectives] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [circuits, setCircuits] = useState({});
  const [bulkheads, setBulkheads] = useState({});
  const [telemetry, setTelemetry] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  // Modals
  const [selectedCheckpoint, setSelectedCheckpoint] = useState(null);
  const [isResumeModalOpen, setIsResumeModalOpen] = useState(false);
  const [isExperimentModalOpen, setIsExperimentModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      const [
        ovRes,
        compRes,
        chkRes,
        expRes,
        objRes,
        bdgRes,
        cctRes,
        bkhRes,
        telRes,
      ] = await Promise.allSettled([
        reliabilityService.getOverview(),
        reliabilityService.listComponents({ limit: 100 }),
        reliabilityService.listCheckpoints({ limit: 50 }),
        reliabilityService.listExperiments({ limit: 50 }),
        reliabilityService.listObjectives(),
        reliabilityService.listBudgets(),
        reliabilityService.getCircuits(),
        reliabilityService.getBulkheads(),
        reliabilityService.getTelemetry({ days: 14 }),
      ]);

      if (ovRes.status === "fulfilled") setOverview(ovRes.value);
      if (compRes.status === "fulfilled") setComponents(compRes.value || []);
      if (chkRes.status === "fulfilled") setCheckpoints(chkRes.value || []);
      if (expRes.status === "fulfilled") setExperiments(expRes.value || []);
      if (objRes.status === "fulfilled") setObjectives(objRes.value || []);
      if (bdgRes.status === "fulfilled") setBudgets(bdgRes.value || []);
      if (cctRes.status === "fulfilled") setCircuits(cctRes.value || {});
      if (bkhRes.status === "fulfilled") setBulkheads(bkhRes.value || {});
      if (telRes.status === "fulfilled") setTelemetry(telRes.value || null);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load reliability dashboard data.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleOpenResume = (chk) => {
    setSelectedCheckpoint(chk);
    setIsResumeModalOpen(true);
  };

  const handleResumeSuccess = () => {
    fetchData();
  };

  const handleApproveExperiment = async (expId) => {
    try {
      await reliabilityService.approveExperiment(expId);
      fetchData();
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleRunExperiment = async (expId) => {
    try {
      await reliabilityService.runExperiment(expId);
      fetchData();
    } catch (err) {
      alert(`Execution error: ${err.message}`);
    }
  };

  const handleAbortExperiment = async (expId) => {
    try {
      await reliabilityService.abortExperiment(expId, "Aborted from dashboard");
      fetchData();
    } catch (err) {
      alert(`Abort error: ${err.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-7 h-7 text-indigo-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Reliability & Resilience
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Component health, failure classification, checkpoint recovery, circuit breakers, and sandbox chaos engineering.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsExperimentModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" /> New Chaos Experiment
          </button>

          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-200 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Top Overview Cards */}
      <ReliabilityOverviewCards overview={overview} />

      {/* Sub-Navigation Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Link
          href="/app/reliability/components"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">All Components</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
        <Link
          href="/app/reliability/checkpoints"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">Checkpoints & Resumption</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
        <Link
          href="/app/reliability/experiments"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">Chaos Experiments</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
        <Link
          href="/app/reliability/objectives"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">SLOs & Budgets</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800">
        <nav className="flex space-x-6 text-sm">
          <button
            onClick={() => setActiveTab("components")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "components"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Server className="w-4 h-4" /> Components ({components.length})
          </button>

          <button
            onClick={() => setActiveTab("circuits")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "circuits"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Zap className="w-4 h-4" /> Circuits & Bulkheads
          </button>

          <button
            onClick={() => setActiveTab("checkpoints")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "checkpoints"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <RotateCcw className="w-4 h-4" /> Checkpoints ({checkpoints.length})
          </button>

          <button
            onClick={() => setActiveTab("experiments")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "experiments"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FlaskConical className="w-4 h-4" /> Chaos Sandbox ({experiments.length})
          </button>

          <button
            onClick={() => setActiveTab("objectives")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "objectives"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Target className="w-4 h-4" /> SLOs & Budgets
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      {activeTab === "components" && (
        <ComponentListTable components={components} onRefresh={fetchData} />
      )}

      {activeTab === "circuits" && (
        <CircuitBreakerPanel
          circuits={circuits}
          bulkheads={bulkheads}
          onRefresh={fetchData}
        />
      )}

      {activeTab === "checkpoints" && (
        <ExecutionCheckpointTable
          checkpoints={checkpoints}
          onResume={handleOpenResume}
          onRefresh={fetchData}
        />
      )}

      {activeTab === "experiments" && (
        <ChaosExperimentTable
          experiments={experiments}
          onApprove={handleApproveExperiment}
          onRun={handleRunExperiment}
          onAbort={handleAbortExperiment}
          onRefresh={fetchData}
        />
      )}

      {activeTab === "objectives" && (
        <ReliabilityObjectiveTable
          objectives={objectives}
          budgets={budgets}
          onRefresh={fetchData}
        />
      )}

      {/* Modals */}
      <ResumeModal
        checkpoint={selectedCheckpoint}
        isOpen={isResumeModalOpen}
        onClose={() => setIsResumeModalOpen(false)}
        onSuccess={handleResumeSuccess}
      />

      <ChaosExperimentModal
        isOpen={isExperimentModalOpen}
        onClose={() => setIsExperimentModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
}

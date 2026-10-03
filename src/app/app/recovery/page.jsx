"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  LifeBuoy,
  ShieldCheck,
  Archive,
  RotateCcw,
  Plus,
  RefreshCw,
  ArrowRight,
  Layers,
  FlaskConical,
  Target,
  AlertTriangle,
} from "lucide-react";
import { recoveryService } from "@/services/recovery";
import { RecoveryOverviewCards } from "@/components/features/recovery/RecoveryOverviewCards";
import { BackupTable } from "@/components/features/recovery/BackupTable";
import { RestorePlanModal } from "@/components/features/recovery/RestorePlanModal";
import { RestoreRunTable } from "@/components/features/recovery/RestoreRunTable";
import { RecoveryReadinessTable } from "@/components/features/recovery/RecoveryReadinessTable";
import { ContinuityPlanCard } from "@/components/features/recovery/ContinuityPlanCard";
import { RecoveryExerciseTable } from "@/components/features/recovery/RecoveryExerciseTable";
import { RecoveryExerciseModal } from "@/components/features/recovery/RecoveryExerciseModal";

export default function DisasterRecoveryDashboardPage() {
  const [activeTab, setActiveTab] = useState("backups");
  const [overview, setOverview] = useState(null);
  const [backups, setBackups] = useState([]);
  const [restores, setRestores] = useState([]);
  const [readiness, setReadiness] = useState([]);
  const [continuityPlans, setContinuityPlans] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  // Modals
  const [selectedBackupForRestore, setSelectedBackupForRestore] = useState(null);
  const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);
  const [isExerciseModalOpen, setIsExerciseModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      const [ovRes, bkRes, rstRes, rdyRes, ctpRes, exRes] = await Promise.allSettled([
        recoveryService.getOverview(),
        recoveryService.listBackups({ limit: 50 }),
        recoveryService.listRestores({ limit: 50 }),
        recoveryService.getReadiness(),
        recoveryService.listContinuityPlans(),
        recoveryService.listExercises({ limit: 50 }),
      ]);

      if (ovRes.status === "fulfilled") setOverview(ovRes.value);
      if (bkRes.status === "fulfilled") setBackups(bkRes.value || []);
      if (rstRes.status === "fulfilled") setRestores(rstRes.value || []);
      if (rdyRes.status === "fulfilled") setReadiness(rdyRes.value || []);
      if (ctpRes.status === "fulfilled") setContinuityPlans(ctpRes.value || []);
      if (exRes.status === "fulfilled") setExercises(exRes.value || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load disaster recovery dashboard data.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateSnapshot = async () => {
    try {
      await recoveryService.createBackup({ strategy: "logical_export" });
      fetchData();
    } catch (err) {
      alert(`Snapshot error: ${err.message}`);
    }
  };

  const handleVerifyBackup = async (id) => {
    try {
      await recoveryService.verifyBackup(id);
      fetchData();
    } catch (err) {
      alert(`Verification error: ${err.message}`);
    }
  };

  const handleDryRun = (b) => {
    setSelectedBackupForRestore(b);
    setIsRestoreModalOpen(true);
  };

  const handleExpireBackup = async (id) => {
    if (!confirm("Are you sure you want to mark this backup as expired?")) return;
    try {
      await recoveryService.expireBackup(id);
      fetchData();
    } catch (err) {
      alert(`Expiration error: ${err.message}`);
    }
  };

  const handleRunExercise = async (id) => {
    try {
      await recoveryService.runExercise(id);
      fetchData();
    } catch (err) {
      alert(`Exercise run error: ${err.message}`);
    }
  };

  const handleAbortExercise = async (id) => {
    try {
      await recoveryService.abortExercise(id, "Operator aborted from dashboard");
      fetchData();
    } catch (err) {
      alert(`Exercise abort error: ${err.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <LifeBuoy className="w-7 h-7 text-indigo-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Disaster Recovery & Business Continuity
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Application-level logical snapshots, cryptographic integrity verification, guarded restore orchestration, and continuity drills.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleCreateSnapshot}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Archive className="w-4 h-4" /> Create Snapshot
          </button>

          <button
            onClick={() => setIsExerciseModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold shadow-sm transition border border-slate-700"
          >
            <FlaskConical className="w-4 h-4" /> New Drill
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
      <RecoveryOverviewCards overview={overview} />

      {/* Sub-Navigation Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Link
          href="/app/recovery/backups"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">All Backups</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
        <Link
          href="/app/recovery/restores"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">Restore Plans & Runs</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
        <Link
          href="/app/recovery/readiness"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">Readiness Matrix</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
        <Link
          href="/app/recovery/continuity"
          className="p-3 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition flex items-center justify-between text-xs"
        >
          <span className="text-slate-300 font-medium">Continuity Plans</span>
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
        </Link>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-slate-800">
        <nav className="flex space-x-6 text-sm">
          <button
            onClick={() => setActiveTab("backups")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "backups"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Archive className="w-4 h-4" /> Snapshots ({backups.length})
          </button>

          <button
            onClick={() => setActiveTab("readiness")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "readiness"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LifeBuoy className="w-4 h-4" /> Readiness Matrix
          </button>

          <button
            onClick={() => setActiveTab("restores")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "restores"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <RotateCcw className="w-4 h-4" /> Restores ({restores.length})
          </button>

          <button
            onClick={() => setActiveTab("continuity")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "continuity"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-4 h-4" /> Continuity Plans ({continuityPlans.length})
          </button>

          <button
            onClick={() => setActiveTab("exercises")}
            className={`pb-3 font-medium transition flex items-center gap-2 ${
              activeTab === "exercises"
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FlaskConical className="w-4 h-4" /> Exercises & Drills ({exercises.length})
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      {activeTab === "backups" && (
        <BackupTable
          backups={backups}
          onVerify={handleVerifyBackup}
          onDryRun={handleDryRun}
          onExpire={handleExpireBackup}
          onRefresh={fetchData}
        />
      )}

      {activeTab === "readiness" && (
        <RecoveryReadinessTable
          readiness={readiness}
          onRefresh={fetchData}
        />
      )}

      {activeTab === "restores" && (
        <RestoreRunTable restores={restores} onRefresh={fetchData} />
      )}

      {activeTab === "continuity" && (
        <div className="space-y-4">
          {continuityPlans.length === 0 ? (
            <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-500 text-xs">
              No business continuity plans defined. Create an operational recovery sequence.
            </div>
          ) : (
            continuityPlans.map((plan) => (
              <ContinuityPlanCard key={plan.id} plan={plan} />
            ))
          )}
        </div>
      )}

      {activeTab === "exercises" && (
        <RecoveryExerciseTable
          exercises={exercises}
          onRun={handleRunExercise}
          onAbort={handleAbortExercise}
          onRefresh={fetchData}
        />
      )}

      {/* Modals */}
      <RestorePlanModal
        isOpen={isRestoreModalOpen}
        onClose={() => setIsRestoreModalOpen(false)}
        backup={selectedBackupForRestore}
        onSuccess={fetchData}
      />

      <RecoveryExerciseModal
        isOpen={isExerciseModalOpen}
        onClose={() => setIsExerciseModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
}

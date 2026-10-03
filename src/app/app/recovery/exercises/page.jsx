"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, FlaskConical, Plus, RefreshCw } from "lucide-react";
import { recoveryService } from "@/services/recovery";
import { RecoveryExerciseTable } from "@/components/features/recovery/RecoveryExerciseTable";
import { RecoveryExerciseModal } from "@/components/features/recovery/RecoveryExerciseModal";

export default function RecoveryExercisesPage() {
  const [exercises, setExercises] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.listExercises({ limit: 100 });
      setExercises(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load recovery exercises.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRun = async (id) => {
    try {
      await recoveryService.runExercise(id);
      fetchData();
    } catch (err) {
      alert(`Error running exercise: ${err.message}`);
    }
  };

  const handleAbort = async (id) => {
    try {
      await recoveryService.abortExercise(id, "Operator aborted from exercises list");
      fetchData();
    } catch (err) {
      alert(`Error aborting exercise: ${err.message}`);
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
            <FlaskConical className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Disaster Recovery Exercises & Drills
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Simulate platform recovery scenarios in isolated sandbox and staging environments. Production exercises are blocked by default.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" /> New Drill
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

      <RecoveryExerciseTable
        exercises={exercises}
        onRun={handleRun}
        onAbort={handleAbort}
        onRefresh={fetchData}
      />

      <RecoveryExerciseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
}

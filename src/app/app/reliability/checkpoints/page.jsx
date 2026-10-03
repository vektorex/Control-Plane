"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, RotateCcw, RefreshCw, ShieldCheck } from "lucide-react";
import { reliabilityService } from "@/services/reliability";
import { ExecutionCheckpointTable } from "@/components/features/reliability/ExecutionCheckpointTable";
import { ResumeModal } from "@/components/features/reliability/ResumeModal";

export default function ReliabilityCheckpointsPage() {
  const [checkpoints, setCheckpoints] = useState([]);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState(null);
  const [isResumeModalOpen, setIsResumeModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await reliabilityService.listCheckpoints({ limit: 100 });
      setCheckpoints(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load checkpoints.");
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
            <RotateCcw className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Execution Checkpoints & Resumption
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Immutable, sanitized execution boundary state snapshots. Re-evaluates RBAC, security quarantine, and data deletion policies prior to resume.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={isLoading}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          title="Refresh checkpoints"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-200 text-sm">
          {errorMsg}
        </div>
      )}

      <ExecutionCheckpointTable
        checkpoints={checkpoints}
        onResume={handleOpenResume}
        onRefresh={fetchData}
      />

      <ResumeModal
        checkpoint={selectedCheckpoint}
        isOpen={isResumeModalOpen}
        onClose={() => setIsResumeModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Archive, Plus, RefreshCw } from "lucide-react";
import { recoveryService } from "@/services/recovery";
import { BackupTable } from "@/components/features/recovery/BackupTable";
import { RestorePlanModal } from "@/components/features/recovery/RestorePlanModal";

export default function BackupsPage() {
  const [backups, setBackups] = useState([]);
  const [selectedBackupForRestore, setSelectedBackupForRestore] = useState(null);
  const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.listBackups({ limit: 100 });
      setBackups(res || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load backups.");
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

  const handleVerify = async (id) => {
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

  const handleExpire = async (id) => {
    if (!confirm("Are you sure you want to expire this snapshot?")) return;
    try {
      await recoveryService.expireBackup(id);
      fetchData();
    } catch (err) {
      alert(`Expiration error: ${err.message}`);
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
            <Archive className="w-6 h-6 text-indigo-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Backup Snapshots
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Immutable, logical state archives accompanied by SHA-256 cryptographic manifests.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCreateSnapshot}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" /> Create Snapshot
          </button>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh backups"
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

      <BackupTable
        backups={backups}
        onVerify={handleVerify}
        onDryRun={handleDryRun}
        onExpire={handleExpire}
        onRefresh={fetchData}
      />

      <RestorePlanModal
        isOpen={isRestoreModalOpen}
        onClose={() => setIsRestoreModalOpen(false)}
        backup={selectedBackupForRestore}
        onSuccess={fetchData}
      />
    </div>
  );
}

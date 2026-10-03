"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Archive,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  RotateCcw,
  RefreshCw,
  FileText,
  Lock,
} from "lucide-react";
import { recoveryService } from "@/services/recovery";
import { RestorePlanModal } from "@/components/features/recovery/RestorePlanModal";

export default function BackupDetailPage({ params }) {
  const unwrappedParams = use(params);
  const backupId = unwrappedParams.backupId;

  const [backup, setBackup] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await recoveryService.getBackup(backupId);
      setBackup(res);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load backup snapshot.");
    } finally {
      setIsLoading(false);
    }
  }, [backupId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleVerify = async () => {
    try {
      setActionLoading(true);
      await recoveryService.verifyBackup(backupId);
      await fetchData();
    } catch (err) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleExpire = async () => {
    if (!confirm("Are you sure you want to mark this backup snapshot as expired?")) return;
    try {
      setActionLoading(true);
      await recoveryService.expireBackup(backupId);
      await fetchData();
    } catch (err) {
      alert(`Expiration error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading && !backup) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
        Loading backup snapshot details...
      </div>
    );
  }

  if (errorMsg || !backup) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/app/recovery/backups"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Backups
        </Link>
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-200 text-sm">
          {errorMsg || "Backup snapshot not found."}
        </div>
      </div>
    );
  }

  const manifest = backup.manifest;
  const isVerified = manifest?.verification_status === "verified";
  const verifications = backup.verifications || [];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/app/recovery/backups"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Snapshots
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl">
              <Archive className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight font-mono">
                  {backup.id}
                </h1>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                  v{backup.backup_version}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 uppercase font-mono">
                  {backup.classification}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Logical Snapshot • Tenant: {backup.organization_id} • Created: {new Date(backup.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isVerified && backup.status === "completed" && (
              <button
                onClick={handleVerify}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <ShieldCheck className="w-3.5 h-3.5" /> Verify Integrity
              </button>
            )}

            {backup.status === "completed" && (
              <button
                onClick={() => setIsRestoreModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Dry-Run Restore
              </button>
            )}

            {backup.status !== "expired" && (
              <button
                onClick={handleExpire}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950 hover:bg-red-900 text-red-300 text-xs font-semibold border border-red-800 transition disabled:opacity-50"
              >
                Expire
              </button>
            )}

            <button
              onClick={fetchData}
              disabled={isLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh snapshot"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Snapshot Status</span>
          <div className="mt-2 text-sm font-bold text-white uppercase font-mono">
            {backup.status}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            {backup.completed_at ? "Completed successfully" : "In-flight"}
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Asset Inventory</span>
          <div className="mt-2 text-xl font-bold font-mono text-white">
            {backup.resource_count}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            ~{Math.round((backup.byte_estimate || 0) / 1024)} KB payload
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Verification State</span>
          <div className="mt-2">
            {isVerified ? (
              <span className="inline-flex items-center gap-1 text-sm font-bold text-emerald-400">
                <CheckCircle2 className="w-4 h-4" /> Certified Verified
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-sm font-bold text-amber-400">
                <AlertTriangle className="w-4 h-4" /> Unverified
              </span>
            )}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            {verifications.length} checks performed
          </span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 uppercase font-semibold">Restore Eligibility</span>
          <div className="mt-2 text-xs font-semibold text-slate-200">
            {isVerified ? "Eligible (Sandbox & Live)" : "Requires Verification"}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">
            Guarded by Step 32 Governance
          </span>
        </div>
      </div>

      {/* Manifest Specification Card */}
      {manifest && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-300 font-semibold border-b border-slate-800 pb-2">
            <span className="flex items-center gap-2 text-white">
              <FileText className="w-4 h-4 text-indigo-400" /> Cryptographic Manifest
            </span>
            <span className="text-[11px] text-slate-500">{manifest.format}</span>
          </div>

          <div className="space-y-1 text-slate-400">
            <div>
              <span className="text-slate-500">Storage Reference:</span>{" "}
              <span className="text-white">{manifest.storage_reference}</span>
            </div>
            <div>
              <span className="text-slate-500">Content SHA-256:</span>{" "}
              <span className="text-indigo-300">{manifest.content_hash}</span>
            </div>
            <div>
              <span className="text-slate-500">Manifest SHA-256:</span>{" "}
              <span className="text-slate-300">{manifest.manifest_hash}</span>
            </div>
            <div>
              <span className="text-slate-500">Encryption:</span>{" "}
              <span className="text-emerald-400">
                {manifest.encryption_metadata?.encrypted ? "Fernet AES128-CBC Active" : "None (Internal)"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Verifications Log */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Verification & Simulation Checks</h3>
          <span className="text-xs text-slate-500 font-mono">{verifications.length} checks</span>
        </div>

        {verifications.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">
            No verification checks executed yet. Click &quot;Verify Integrity&quot; to run validation battery.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 font-mono text-xs">
            {verifications.map((v) => (
              <div key={v.id} className="p-3.5 flex items-center justify-between hover:bg-slate-800/30">
                <div className="space-y-0.5">
                  <div className="font-semibold text-white uppercase tracking-wider text-[11px]">
                    {v.verification_type.replace(/_/g, " ")}
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    {v.details?.message || v.details?.content || JSON.stringify(v.details)}
                  </div>
                </div>
                <div className="text-right">
                  {v.status === "passed" ? (
                    <span className="text-emerald-400 font-bold uppercase">PASSED</span>
                  ) : v.status === "warning" ? (
                    <span className="text-amber-400 font-bold uppercase">WARNING</span>
                  ) : (
                    <span className="text-red-400 font-bold uppercase">FAILED</span>
                  )}
                  <span className="text-[10px] text-slate-500 block">
                    {new Date(v.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <RestorePlanModal
        isOpen={isRestoreModalOpen}
        onClose={() => setIsRestoreModalOpen(false)}
        backup={backup}
        onSuccess={fetchData}
      />
    </div>
  );
}

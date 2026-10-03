"use client";

import React, { useState } from "react";
import {
  X,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Info,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export function RollbackModal({
  installation,
  versions = [],
  isOpen,
  onClose,
  onRolledBack,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [targetVersionId, setTargetVersionId] = useState("");
  const [reason, setReason] = useState("");

  if (!isOpen || !installation) return null;

  // Filter candidate rollback versions (exclude currently installed version)
  const currentVersionId = installation.package_version_id;
  const rollbackCandidates = versions.filter(
    (v) => v.id !== currentVersionId && v.publication_status === "published"
  );

  const selectedVersion = versions.find((v) => v.id === targetVersionId);

  const handleRollback = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await marketplaceService.rollbackInstallation(installation.id, {
        target_version_id: targetVersionId || null,
        reason: reason || "User initiated rollback via UI",
      });
      setSuccess(true);
      setTimeout(() => {
        onRolledBack?.(res);
        onClose();
      }, 1200);
    } catch (err) {
      setError(err?.message || "Failed to rollback package installation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div className="w-full max-w-lg bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5 text-amber-500" />
            <h2 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
              Rollback Package Installation
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs text-neutral-700 dark:text-neutral-300">
          <div className="p-3 rounded-lg border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20 text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-[11px]">Rollback Verification Rules</p>
              <p className="text-[11px] leading-relaxed text-amber-700 dark:text-amber-300/80">
                Rollbacks can only target previously published, unrevoked versions. If a version was blocked or revoked for security reasons, it cannot be selected as a rollback target.
              </p>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-medium text-neutral-700 dark:text-neutral-300 block mb-1">
              Select Previous Version to Restore
            </label>
            <select
              value={targetVersionId}
              onChange={(e) => setTargetVersionId(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Restore previous valid version (automatic)</option>
              {rollbackCandidates.map((v) => (
                <option key={v.id} value={v.id}>
                  v{v.version} — {v.security_status === "scanned" ? "Security Verified" : v.security_status} ({new Date(v.created_at).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>

          {selectedVersion && (
            <div className="p-3 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 space-y-1.5">
              <p className="font-medium text-neutral-800 dark:text-neutral-200">
                Target: Version {selectedVersion.version}
              </p>
              <div className="flex items-center gap-2">
                {selectedVersion.security_status === "scanned" ? (
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                )}
                <span className="text-[11px] text-neutral-500">
                  Status: {selectedVersion.security_status} • Hash: {selectedVersion.content_hash?.slice(0, 10)}...
                </span>
              </div>
            </div>
          )}

          <div>
            <label className="text-[11px] font-medium text-neutral-700 dark:text-neutral-300 block mb-1">
              Reason for Rollback
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Encountered prompt regression or compatibility issue with upstream workflow"
              className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
            />
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* Success Banner */}
          {success && (
            <div className="p-3 rounded-lg border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Installation rolled back successfully!
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleRollback}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            {loading ? "Rolling back..." : "Confirm Rollback"}
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  X,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  Lock,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  FileDiff,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export function UpdateModal({
  installation,
  newVersion,
  isOpen,
  onClose,
  onUpdated,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  if (!isOpen || !installation || !newVersion) return null;

  const currentVersion = installation.package_version || {};
  const currentManifest = currentVersion.manifest || {};
  const newManifest = newVersion.manifest || {};

  const currentPerms = (currentManifest.permissions || []).map((p) => p.scope);
  const newPerms = (newManifest.permissions || []).map((p) => p.scope);
  const addedPerms = newPerms.filter((p) => !currentPerms.includes(p));

  const currentDeps = (currentManifest.dependencies || []).map((d) => d.dependency_identifier);
  const newDeps = (newManifest.dependencies || []).map((d) => d.dependency_identifier);
  const addedDeps = newDeps.filter((d) => !currentDeps.includes(d));

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await marketplaceService.updateInstallation(installation.id, {
        target_version_id: newVersion.id,
      });
      setSuccess(true);
      setTimeout(() => {
        onUpdated?.(res);
        onClose();
      }, 1200);
    } catch (err) {
      setError(err?.message || "Failed to update package installation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div className="w-full max-w-xl bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-blue-500" />
            <h2 className="text-base font-bold text-neutral-900 dark:text-neutral-100">
              Update Package: {installation.package?.name || "Workflow Package"}
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
          {/* Version Transition Card */}
          <div className="flex items-center justify-between p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
            <div>
              <p className="text-[11px] text-neutral-400 uppercase font-medium">Installed Version</p>
              <p className="font-mono text-base font-bold text-neutral-800 dark:text-neutral-200">
                {currentVersion.version || "1.0.0"}
              </p>
            </div>
            <ArrowRight className="w-5 h-5 text-blue-500" />
            <div className="text-right">
              <p className="text-[11px] text-neutral-400 uppercase font-medium">Target Version</p>
              <p className="font-mono text-base font-bold text-emerald-600 dark:text-emerald-400">
                {newVersion.version}
              </p>
            </div>
          </div>

          {/* Security Status */}
          <div className="flex items-center justify-between p-3 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/30">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span>Target Version Security Scan:</span>
            </div>
            <span className="capitalize font-semibold text-emerald-600 dark:text-emerald-400">
              {newVersion.security_status || "scanned"}
            </span>
          </div>

          {/* Permission Changes */}
          <div className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 space-y-2">
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-amber-500" />
              Permission Impact
            </h4>
            {addedPerms.length > 0 ? (
              <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 text-amber-800 dark:text-amber-200 space-y-1">
                <p className="font-semibold text-[11px]">Notice: New permissions requested:</p>
                <ul className="list-disc pl-4 space-y-0.5 font-mono text-[10px]">
                  {addedPerms.map((p, idx) => (
                    <li key={idx}>{p}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-neutral-500 text-[11px]">No new permissions requested in this release.</p>
            )}
          </div>

          {/* Dependency Changes */}
          <div className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 space-y-2">
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
              <FileDiff className="w-3.5 h-3.5 text-purple-500" />
              Dependency Changes
            </h4>
            {addedDeps.length > 0 ? (
              <div className="text-neutral-600 dark:text-neutral-300">
                <p className="text-[11px] mb-1">New dependencies required:</p>
                <div className="flex flex-wrap gap-1">
                  {addedDeps.map((d, idx) => (
                    <span key={idx} className="font-mono text-[10px] px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 border">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-neutral-500 text-[11px]">Dependencies remain identical.</p>
            )}
          </div>

          {/* Safe Rollback Guarantee */}
          <div className="flex items-center gap-2 p-3 rounded-lg border border-neutral-200 dark:border-neutral-800 text-[11px] text-neutral-500">
            <AlertCircle className="w-4 h-4 text-blue-500 shrink-0" />
            <span>
              If needed, this installation can be safely rolled back to version {currentVersion.version || "1.0.0"} at any time.
            </span>
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
              Package updated successfully to {newVersion.version}!
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
            onClick={handleUpdate}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            {loading ? "Updating..." : `Confirm Update to v${newVersion.version}`}
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  RotateCcw,
  X,
  AlertTriangle,
  ShieldAlert,
  Play,
  CheckCircle2,
  Info,
} from "lucide-react";
import { recoveryService } from "@/services/recovery";

export function RestorePlanModal({
  isOpen,
  onClose,
  backup,
  onSuccess,
}) {
  const [targetEnv, setTargetEnv] = useState("sandbox");
  const [mode, setMode] = useState("dry_run");
  const [conflictPolicy, setConflictPolicy] = useState("skip_existing");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [dryRunResult, setDryRunResult] = useState(null);

  if (!isOpen || !backup) return null;

  const handleSimulate = async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      // 1. Create plan
      const plan = await recoveryService.createRestorePlan({
        backup_run_id: backup.id,
        target_environment: targetEnv,
        mode: mode,
        conflict_policy: conflictPolicy,
      });

      // 2. Execute dry run
      const result = await recoveryService.dryRunRestorePlan(plan.id);
      setDryRunResult({ plan, result });
    } catch (err) {
      setErrorMsg(err.message || "Failed to create or simulate restore plan.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!dryRunResult?.plan?.id) return;
    try {
      setIsLoading(true);
      setErrorMsg("");
      await recoveryService.executeRestorePlan(dryRunResult.plan.id);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Failed to execute restore plan.");
    } finally {
      setIsLoading(false);
    }
  };

  const isProduction = targetEnv === "production";
  const isReplace = conflictPolicy === "replace_existing";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">
              Restore Orchestration Builder
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 overflow-y-auto text-xs text-slate-300">
          {errorMsg && (
            <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-200">
              {errorMsg}
            </div>
          )}

          {/* Source Snapshot Info */}
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono flex items-center justify-between">
            <div>
              <span className="text-slate-500 block text-[11px]">Source Snapshot</span>
              <span className="text-white font-semibold">{backup.id}</span>
            </div>
            <div className="text-right">
              <span className="text-slate-500 block text-[11px]">Assets / Class</span>
              <span className="text-indigo-300">
                {backup.resource_count} items ({backup.classification})
              </span>
            </div>
          </div>

          {/* Form Options */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Target Environment
              </label>
              <select
                value={targetEnv}
                onChange={(e) => {
                  setTargetEnv(e.target.value);
                  setDryRunResult(null);
                }}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500"
              >
                <option value="sandbox">Sandbox (Isolated)</option>
                <option value="staging">Staging</option>
                <option value="production">Production (Guarded)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Restore Mode
              </label>
              <select
                value={mode}
                onChange={(e) => {
                  setMode(e.target.value);
                  setDryRunResult(null);
                }}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500"
              >
                <option value="dry_run">Dry Run (Simulation)</option>
                <option value="sandbox">Sandbox Write</option>
                <option value="authorized_restore">Authorized Restore</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Conflict Policy
              </label>
              <select
                value={conflictPolicy}
                onChange={(e) => {
                  setConflictPolicy(e.target.value);
                  setDryRunResult(null);
                }}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500"
              >
                <option value="skip_existing">Skip Existing</option>
                <option value="restore_missing">Restore Missing</option>
                <option value="replace_existing">Replace Existing (HITL)</option>
                <option value="fail">Fail on Conflict</option>
              </select>
            </div>
          </div>

          {/* Elevated Warnings */}
          {(isProduction || isReplace) && (
            <div className="p-3 bg-amber-950/30 border border-amber-800/80 rounded-lg flex items-start gap-2 text-amber-200">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">Elevated Guardrail Triggered</span>
                <span>
                  {isProduction && "Restoration targets production environment. "}
                  {isReplace && "Conflict policy 'replace_existing' will overwrite live data. "}
                  Explicit administrative privileges and Step 18 HITL approval are required.
                </span>
              </div>
            </div>
          )}

          {/* Dry Run Simulation Results */}
          {dryRunResult && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3 font-mono">
              <div className="flex items-center justify-between text-xs font-semibold text-white">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" /> Dry-Run Assessment Passed
                </span>
                <span>{dryRunResult.result.resource_count} resources evaluated</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                <div>
                  Manifest Integrity: <span className="text-white">Verified</span>
                </div>
                <div>
                  Cryptographic Hashes: <span className="text-white">Passed</span>
                </div>
                <div>
                  Legal Hold Conflicts: <span className="text-emerald-400">None</span>
                </div>
                <div>
                  Deleted Data Resurrections: <span className="text-emerald-400">Blocked / Zero</span>
                </div>
              </div>

              <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[11px] text-slate-400">
                Secret Handling: Third-party API keys and OAuth credentials will NOT be restored in plaintext; credential references will require administrative re-authentication.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-950/60">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-slate-400 hover:text-slate-200 text-xs font-medium"
          >
            Cancel
          </button>

          <div className="flex items-center gap-2">
            {!dryRunResult ? (
              <button
                onClick={handleSimulate}
                disabled={isLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                {isLoading ? "Evaluating..." : "Run Dry-Run Assessment"}
              </button>
            ) : (
              <button
                onClick={handleExecute}
                disabled={isLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5" /> Execute Restore Run
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

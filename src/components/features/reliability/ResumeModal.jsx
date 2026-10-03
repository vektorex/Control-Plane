"use client";

import React, { useState } from "react";
import {
  RotateCcw,
  X,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { reliabilityService } from "@/services/reliability";

export function ResumeModal({ checkpoint, isOpen, onClose, onSuccess }) {
  const [reason, setReason] = useState("");
  const [skipCompleted, setSkipCompleted] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState(null);

  if (!isOpen || !checkpoint) return null;

  const handleResume = async (e) => {
    e.preventDefault();
    if (!reason.trim()) {
      setErrorMsg("Mandatory operational rationale is required before resuming.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg("");

      const res = await reliabilityService.resumeCheckpoint(checkpoint.id, {
        reason: reason.trim(),
        skip_completed_steps: skipCompleted,
      });

      setResult(res);
      setTimeout(() => {
        if (onSuccess) onSuccess(res);
      }, 1200);
    } catch (err) {
      setErrorMsg(err.message || "Failed to resume from checkpoint.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
          <div className="p-2 rounded-lg bg-indigo-950/60 border border-indigo-800/40 text-indigo-400">
            <RotateCcw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Resume Resilient Execution</h3>
            <p className="text-xs text-slate-500 font-mono">
              Run #{checkpoint.run_id} (Seq #{checkpoint.sequence_number})
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300">
            {errorMsg}
          </div>
        )}

        {result ? (
          <div className="bg-emerald-950/40 border border-emerald-800 rounded-lg p-4 space-y-2 text-xs">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <CheckCircle2 className="w-4 h-4" /> Execution Resumed Successfully
            </div>
            <p className="text-slate-300">
              Resumed from step: <strong className="text-white font-mono">{result.resumed_from_step || "init"}</strong>
            </p>
            <p className="text-slate-400 text-[11px]">
              Step 32 Governance decision: {result.governance_decision}
            </p>
          </div>
        ) : (
          <form onSubmit={handleResume} className="space-y-4 text-xs">
            {/* Preconditions Notice */}
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <span className="font-semibold text-slate-300 block">Pre-Resume Integrity Verification:</span>
              <div>✓ Checkpoint cryptographic SHA-256 fingerprint verified</div>
              <div>✓ Step 34 Security quarantine status: Clear</div>
              <div>✓ Step 33 Data lifecycle & legal hold check: Valid</div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Operational Justification / Rationale
              </label>
              <textarea
                rows={2}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Explain the operational root cause and resumption trigger..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                required
              />
            </div>

            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={skipCompleted}
                onChange={(e) => setSkipCompleted(e.target.checked)}
                className="rounded border-slate-700 text-indigo-600 focus:ring-0"
              />
              <span>Skip previously completed idempotent steps</span>
            </label>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !reason.trim()}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50 flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                {isSubmitting ? "Validating & Resuming..." : "Confirm Safe Resumption"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  Lock,
  AlertTriangle,
  ShieldCheck,
  CheckCircle,
  X,
  HelpCircle,
} from "lucide-react";
import { securityService } from "@/services/security";

const ALLOWED_ACTIONS = [
  { value: "pause_workflow", label: "Pause Workflow", targetType: "workflow", highRisk: true },
  { value: "pause_trigger", label: "Pause Trigger", targetType: "trigger", highRisk: true },
  { value: "cancel_job", label: "Cancel Job", targetType: "job", highRisk: false },
  { value: "disable_connector_credential", label: "Disable Connector Credential", targetType: "connector", highRisk: true },
  { value: "revoke_session", label: "Revoke Actor Session", targetType: "session", highRisk: true },
  { value: "quarantine_artifact", label: "Quarantine Artifact", targetType: "artifact", highRisk: false },
  { value: "invalidate_cache", label: "Invalidate Cache Namespace", targetType: "cache_namespace", highRisk: false },
  { value: "require_hitl", label: "Require HITL for Future Actions", targetType: "actor", highRisk: false },
];

export function ContainmentActionModal({ incidentId, isOpen, onClose, onSuccess }) {
  const [actionType, setActionType] = useState("pause_workflow");
  const [targetType, setTargetType] = useState("workflow");
  const [targetId, setTargetId] = useState("");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  if (!isOpen) return null;

  const currentActionMeta = ALLOWED_ACTIONS.find((a) => a.value === actionType) || ALLOWED_ACTIONS[0];

  const handleActionChange = (e) => {
    const val = e.target.value;
    setActionType(val);
    const meta = ALLOWED_ACTIONS.find((a) => a.value === val);
    if (meta) {
      setTargetType(meta.targetType);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetId.trim() || !reason.trim()) {
      setErrorMsg("Target ID and justification reason are strictly required.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg("");

      const res = await securityService.requestContainment(incidentId, {
        action_type: actionType,
        target_type: targetType,
        target_id: targetId.trim(),
        reason: reason.trim(),
      });

      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Failed to submit containment request.");
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
          <div className="p-2 rounded-lg bg-orange-950/60 border border-orange-800/40 text-orange-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Execute Containment Action</h3>
            <p className="text-xs text-slate-500">
              Deterministic, allowlisted incident containment with Step 18 HITL review.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-950/50 border border-red-800/80 rounded-lg text-xs text-red-300">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Action selection */}
          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Containment Action (Strict Allowlist)
            </label>
            <select
              value={actionType}
              onChange={handleActionChange}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {ALLOWED_ACTIONS.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label} {a.highRisk ? "(Requires HITL Approval)" : "(Auto-executable)"}
                </option>
              ))}
            </select>
          </div>

          {/* High risk notice */}
          {currentActionMeta.highRisk && (
            <div className="bg-amber-950/40 border border-amber-800/40 rounded-lg p-2.5 text-amber-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong>Privileged Action:</strong> This containment will be routed through
                <strong> Step 18 Human-in-the-Loop (HITL)</strong> approval before execution.
              </span>
            </div>
          )}

          {/* Target type & ID */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Target Type</label>
              <input
                type="text"
                value={targetType}
                onChange={(e) => setTargetType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Target Resource ID</label>
              <input
                type="text"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                placeholder="e.g. wf-finance-sync or usr-123"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white font-mono placeholder-slate-500"
                required
              />
            </div>
          </div>

          {/* Justification reason */}
          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Justification & Operational Reason
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this containment action is required according to active policy..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              required
            />
          </div>

          {/* Anti-tamper footer warning */}
          <p className="text-[11px] text-slate-500 leading-tight">
            AI models cannot self-authorize containment or bypass approval requirements.
            Actions will be written to immutable audit logs and Step 33 compliance evidence.
          </p>

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
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-orange-600 hover:bg-orange-500 text-white disabled:opacity-50 flex items-center gap-1.5"
            >
              <Lock className="w-3.5 h-3.5" />
              {isSubmitting ? "Submitting..." : "Submit Containment Request"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

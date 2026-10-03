"use client";

import React, { useState } from "react";
import { Trash2, X, AlertOctagon } from "lucide-react";

export function DeletionRequestModal({ isOpen, onClose, onSubmit, assets = [] }) {
  const [scopeType, setScopeType] = useState("asset");
  const [scopeId, setScopeId] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!scopeId.trim() || !reason.trim()) return;

    try {
      setSubmitting(true);
      await onSubmit({
        scope_type: scopeType,
        scope_id: scopeId,
        reason,
      });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Trash2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Safe Deletion Request</h3>
              <p className="text-xs text-slate-400">Governance-checked, verifiable deletion workflow</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Deletion Scope Type *
            </label>
            <select
              value={scopeType}
              onChange={(e) => {
                setScopeType(e.target.value);
                setScopeId("");
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-rose-500"
            >
              <option value="asset">Single Logical Asset</option>
              <option value="project">Project Scope</option>
              <option value="workspace">Entire Workspace</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Target Identifier ({scopeType === "asset" ? "Asset ID" : `${scopeType} ID`}) *
            </label>
            {scopeType === "asset" && assets.length > 0 ? (
              <select
                value={scopeId}
                onChange={(e) => setScopeId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-rose-500"
              >
                <option value="">Select an asset...</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.resource_type})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                required
                placeholder={`Enter ${scopeType} ID...`}
                value={scopeId}
                onChange={(e) => setScopeId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
              />
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Deletion Justification / Reason *
            </label>
            <textarea
              required
              rows={3}
              placeholder="e.g. GDPR right-to-be-forgotten request, project decommissioning, or policy retention expiration..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
          </div>

          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-start gap-2">
            <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              All deletion requests are verified against active legal holds, governance authorization policies, and cache/memory dependency trees before execution.
            </span>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !scopeId.trim() || !reason.trim()}
              className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-medium transition-colors"
            >
              {submitting ? "Submitting..." : "Submit Deletion Request"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

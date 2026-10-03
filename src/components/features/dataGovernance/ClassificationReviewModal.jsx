"use client";

import React, { useState } from "react";
import { ShieldCheck, X, AlertTriangle } from "lucide-react";

export function ClassificationReviewModal({
  isOpen,
  onClose,
  onSubmit,
  asset = null,
}) {
  const [classification, setClassification] = useState(
    asset?.data_classification || "internal"
  );
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !asset) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) return;

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit({
        asset_id: asset.id,
        classification,
        reason,
      });
      onClose();
    } catch (err) {
      setError(err?.message || "Failed to update classification.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Review Data Classification</h3>
              <p className="text-xs text-slate-400">Authoritative classification update</p>
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
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Asset Name
            </label>
            <div className="text-sm text-slate-100 font-medium px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-lg">
              {asset.name}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              New Classification Level *
            </label>
            <select
              value={classification}
              onChange={(e) => setClassification(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            >
              <option value="public">Public - Freely shareable externally</option>
              <option value="internal">Internal - Workspace and tenant visibility</option>
              <option value="confidential">Confidential - Restricted to authorized teams</option>
              <option value="restricted">Restricted - Highly regulated; requires approval to access/export</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Authoritative Reason / Review Notes *
            </label>
            <textarea
              required
              rows={3}
              placeholder="Explain the justification for modifying or downgrading this data classification..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              Automated classification cannot silently downgrade confidential or restricted data. Only explicit authorized review actions may alter protection levels.
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
              disabled={submitting || !reason.trim()}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium transition-colors"
            >
              {submitting ? "Saving..." : "Apply Classification"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

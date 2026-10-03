"use client";

import React, { useState } from "react";
import { Lock, X, AlertTriangle } from "lucide-react";

export function LegalHoldModal({ isOpen, onClose, onSubmit, assets = [] }) {
  const [name, setName] = useState("");
  const [reason, setReason] = useState("");
  const [selectedAssetIds, setSelectedAssetIds] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !reason.trim()) return;

    try {
      setSubmitting(true);
      await onSubmit({
        name,
        reason,
        asset_ids: selectedAssetIds,
      });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  const toggleAsset = (id) => {
    setSelectedAssetIds((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Create Legal Hold</h3>
              <p className="text-xs text-slate-400">Strictly prevents deletion of associated data</p>
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
              Hold Name / Matter Identifier *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Litigation Matter 2026-Alpha"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Legal Rationale / Justification *
            </label>
            <textarea
              required
              rows={3}
              placeholder="Detail the preservation requirements, regulatory notice, or dispute details..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select Assets to Protect ({selectedAssetIds.length} selected)
            </label>
            <div className="max-h-36 overflow-y-auto space-y-1 p-2 bg-slate-950/60 border border-slate-800 rounded-lg">
              {assets.map((asset) => (
                <label
                  key={asset.id}
                  className="flex items-center gap-2 p-1.5 rounded hover:bg-slate-800/40 text-xs text-slate-300 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedAssetIds.includes(asset.id)}
                    onChange={() => toggleAsset(asset.id)}
                    className="rounded border-slate-700 text-amber-500 focus:ring-amber-500/20"
                  />
                  <span className="truncate">{asset.name}</span>
                  <span className="ml-auto text-[10px] text-slate-500 font-mono">
                    {asset.asset_type}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              Assets under an active legal hold cannot be deleted by automated retention policies or user deletion requests until explicitly released.
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
              disabled={submitting || !name.trim() || !reason.trim()}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-medium transition-colors"
            >
              {submitting ? "Applying Hold..." : "Apply Legal Hold"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

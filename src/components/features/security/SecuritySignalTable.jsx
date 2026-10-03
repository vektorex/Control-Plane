"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Clock,
  Eye,
  CheckCircle,
  XCircle,
  Filter,
  User,
  Shield,
  Layers,
} from "lucide-react";
import { securityService } from "@/services/security";

export function SecuritySignalTable({ signals = [], onRefresh }) {
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [dismissReason, setDismissReason] = useState("");
  const [isDismissing, setIsDismissing] = useState(false);

  const filtered = signals.filter((sig) => {
    if (filterSeverity !== "all" && sig.severity !== filterSeverity) return false;
    if (filterType !== "all" && sig.signal_type !== filterType) return false;
    return true;
  });

  const handleDismiss = async () => {
    if (!selectedSignal || !dismissReason.trim()) return;
    try {
      setIsDismissing(true);
      await securityService.updateSignal(selectedSignal.id, {
        status: "dismissed",
        dismissal_reason: dismissReason,
      });
      setSelectedSignal(null);
      setDismissReason("");
      if (onRefresh) onRefresh();
    } catch (err) {
      alert("Failed to dismiss signal: " + (err.message || err));
    } finally {
      setIsDismissing(false);
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case "critical":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-950 text-red-400 border border-red-800">Critical</span>;
      case "high":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-950 text-amber-400 border border-amber-800">High</span>;
      case "medium":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-yellow-950/80 text-yellow-400 border border-yellow-800">Medium</span>;
      case "low":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-950/80 text-blue-400 border border-blue-800">Low</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-800 text-slate-300">Info</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Filters bar */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">Filters:</span>

          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Signal Types</option>
            <option value="prompt_injection">Prompt Injection</option>
            <option value="secret_detection">Secret Detection</option>
            <option value="pii_exposure">PII Exposure</option>
            <option value="authorization_denied">Authorization Denied</option>
            <option value="authentication_failure">Authentication Failure</option>
            <option value="tool_abuse">Tool Abuse</option>
            <option value="connector_abuse">Connector Abuse</option>
            <option value="suspicious_workflow">Suspicious Workflow</option>
            <option value="legal_hold_bypass_attempt">Legal Hold Bypass</option>
            <option value="tenant_isolation_violation">Tenant Isolation Violation</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Showing {filtered.length} of {signals.length} signals
        </div>
      </div>

      {/* Signals Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Signal Type</th>
              <th className="py-3 px-4 font-semibold">Severity</th>
              <th className="py-3 px-4 font-semibold">Source</th>
              <th className="py-3 px-4 font-semibold">Actor</th>
              <th className="py-3 px-4 font-semibold">Confidence</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Detected At</th>
              <th className="py-3 px-4 font-semibold text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-500">
                  No security signals match current filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((sig) => (
                <tr key={sig.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-mono text-xs font-semibold text-white">
                      {sig.signal_type}
                    </div>
                    <div className="text-xs text-slate-500 font-mono">
                      {sig.id.substring(0, 8)}...
                    </div>
                  </td>
                  <td className="py-3 px-4">{getSeverityBadge(sig.severity)}</td>
                  <td className="py-3 px-4">
                    <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                      {sig.source_type}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5 text-xs text-slate-300">
                      <User className="w-3.5 h-3.5 text-slate-500" />
                      <span>{sig.actor_id || "system"}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-mono text-slate-400">
                      {Math.round(sig.confidence * 100)}%
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs capitalize font-medium text-slate-400">
                      {sig.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(sig.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setSelectedSignal(sig)}
                      className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition-colors"
                      title="Inspect Signal"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Signal Inspector Modal */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 space-y-4 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-400" />
                  Signal Details
                </h3>
                <p className="text-xs font-mono text-slate-500">{selectedSignal.id}</p>
              </div>
              <button
                onClick={() => setSelectedSignal(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                <div>
                  <span className="text-slate-500 block">Signal Type</span>
                  <strong className="text-white font-mono">{selectedSignal.signal_type}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Severity & Confidence</span>
                  <div className="flex items-center gap-2 mt-0.5">
                    {getSeverityBadge(selectedSignal.severity)}
                    <span className="text-slate-400 font-mono">
                      {Math.round(selectedSignal.confidence * 100)}%
                    </span>
                  </div>
                </div>
                <div>
                  <span className="text-slate-500 block">Source & ID</span>
                  <span className="text-slate-300 font-mono">
                    {selectedSignal.source_type} ({selectedSignal.source_id || "none"})
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Actor</span>
                  <span className="text-slate-300 font-mono">
                    {selectedSignal.actor_type || "actor"}: {selectedSignal.actor_id || "anonymous"}
                  </span>
                </div>
              </div>

              {/* Justification Reasons */}
              <div>
                <span className="text-slate-400 font-semibold block mb-1">
                  Deterministic Policy Reasons:
                </span>
                <ul className="list-disc list-inside space-y-1 bg-slate-950 p-2.5 rounded border border-slate-800 text-slate-300">
                  {(selectedSignal.metadata?.reasons || ["Deterministic threshold exceeded"]).map(
                    (r, i) => (
                      <li key={i}>{r}</li>
                    )
                  )}
                </ul>
              </div>

              {/* Correlation metadata */}
              <div>
                <span className="text-slate-400 font-semibold block mb-1">Correlation Context:</span>
                <pre className="bg-slate-950 p-2.5 rounded border border-slate-800 text-slate-300 overflow-x-auto text-[11px]">
                  {JSON.stringify(
                    {
                      request_id: selectedSignal.request_id,
                      correlation_id: selectedSignal.correlation_id,
                      causation_id: selectedSignal.causation_id,
                      metadata: selectedSignal.metadata,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>

              {/* False Positive Dismissal Box */}
              {selectedSignal.status !== "dismissed" && (
                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <label className="block text-slate-400 font-medium">
                    Dismiss as Benign / False Positive:
                  </label>
                  <input
                    type="text"
                    value={dismissReason}
                    onChange={(e) => setDismissReason(e.target.value)}
                    placeholder="Document mandatory dismissal rationale..."
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <div className="flex justify-end gap-2 pt-1">
                    <button
                      onClick={() => setSelectedSignal(null)}
                      className="px-3 py-1.5 text-xs rounded border border-slate-700 text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDismiss}
                      disabled={!dismissReason.trim() || isDismissing}
                      className="px-3 py-1.5 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 disabled:opacity-50"
                    >
                      {isDismissing ? "Dismissing..." : "Confirm Dismissal"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

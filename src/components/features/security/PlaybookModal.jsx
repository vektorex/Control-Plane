"use client";

import React, { useState } from "react";
import {
  BookOpen,
  X,
  Plus,
  Play,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { securityService } from "@/services/security";

const PLAYBOOK_ALLOWED_ACTIONS = [
  "create_incident",
  "increase_logging",
  "block_job",
  "pause_workflow",
  "disable_trigger",
  "require_approval",
  "invalidate_cache",
  "revoke_session",
  "disable_connector_credential",
  "quarantine_artifact",
  "notify_admin",
  "create_privacy_request",
  "create_governance_review",
];

export function PlaybookModal({ isOpen, onClose, onSuccess }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [signalType, setSignalType] = useState("prompt_injection");
  const [minSeverity, setMinSeverity] = useState("high");
  const [selectedActions, setSelectedActions] = useState(["create_incident"]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  if (!isOpen) return null;

  const toggleAction = (act) => {
    if (selectedActions.includes(act)) {
      if (selectedActions.length > 1) {
        setSelectedActions(selectedActions.filter((a) => a !== act));
      }
    } else {
      setSelectedActions([...selectedActions, act]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMsg("Playbook name is required.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg("");

      const triggerConditions = {
        signal_type: signalType,
        min_severity: minSeverity,
      };

      const res = await securityService.createPlaybook({
        name: name.trim(),
        description: description.trim(),
        trigger_conditions: triggerConditions,
        actions: selectedActions,
        enabled: true,
      });

      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Failed to create playbook.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
          <div className="p-2 rounded-lg bg-indigo-950/60 border border-indigo-800/40 text-indigo-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Create Response Playbook</h3>
            <p className="text-xs text-slate-500">
              Define deterministic trigger conditions and allowlisted security actions.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-950/50 border border-red-800/80 rounded-lg text-xs text-red-300">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Playbook Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Prompt Injection Containment Playbook"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what scenario this playbook mitigates..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Trigger Signal Type</label>
              <select
                value={signalType}
                onChange={(e) => setSignalType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
              >
                <option value="prompt_injection">Prompt Injection</option>
                <option value="secret_detection">Secret Detection</option>
                <option value="pii_exposure">PII Exposure</option>
                <option value="tool_abuse">Tool Abuse</option>
                <option value="connector_abuse">Connector Abuse</option>
                <option value="suspicious_workflow">Suspicious Workflow</option>
                <option value="data_export_anomaly">Data Export Anomaly</option>
                <option value="privilege_escalation_attempt">Privilege Escalation</option>
                <option value="legal_hold_bypass_attempt">Legal Hold Bypass</option>
                <option value="tenant_isolation_violation">Tenant Isolation Violation</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Minimum Severity</label>
              <select
                value={minSeverity}
                onChange={(e) => setMinSeverity(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Select Response Actions (Strict Allowlist)
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto p-2 bg-slate-950 rounded-lg border border-slate-800">
              {PLAYBOOK_ALLOWED_ACTIONS.map((act) => {
                const checked = selectedActions.includes(act);
                return (
                  <label
                    key={act}
                    className={`flex items-center gap-2 p-1.5 rounded cursor-pointer transition-colors ${
                      checked ? "bg-indigo-950/60 border border-indigo-700/50 text-indigo-300" : "hover:bg-slate-900 text-slate-400"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleAction(act)}
                      className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                    />
                    <span className="font-mono text-[11px] truncate">{act}</span>
                  </label>
                );
              })}
            </div>
          </div>

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
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Save Playbook"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

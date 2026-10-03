"use client";

import React, { useState } from "react";
import { FlaskConical, X, AlertTriangle, ShieldAlert } from "lucide-react";
import { recoveryService } from "@/services/recovery";

export function RecoveryExerciseModal({ isOpen, onClose, onSuccess }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [scenario, setScenario] = useState("database_restore_simulation");
  const [environment, setEnvironment] = useState("sandbox");
  const [expectedRecovery, setExpectedRecovery] = useState(
    "Verify state deserialization, foreign key integrity, and zero production data mutation."
  );
  const [abortConditions, setAbortConditions] = useState(
    "Abort immediately if unexpected network calls or mutation attempts occur."
  );
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setIsLoading(true);
      setErrorMsg("");

      await recoveryService.createExercise({
        name,
        description,
        scenario,
        environment,
        expected_recovery: expectedRecovery,
        abort_conditions: abortConditions,
      });

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Failed to create recovery exercise.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">
              Create Recovery Exercise
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {errorMsg && (
            <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-200">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Exercise Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Sandbox PostgreSQL Outage Drill"
              className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Scenario
              </label>
              <select
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500 font-mono"
              >
                <option value="database_restore_simulation">Database Restore</option>
                <option value="workflow_recovery">Workflow Recovery</option>
                <option value="job_recovery">Job Recovery</option>
                <option value="event_recovery">Event Recovery</option>
                <option value="artifact_recovery">Artifact Recovery</option>
                <option value="provider_outage_recovery">Provider Outage</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Environment
              </label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500 font-mono"
              >
                <option value="sandbox">Sandbox (Safe)</option>
                <option value="test">Test</option>
                <option value="staging">Staging</option>
                <option value="production">Production (Requires HITL)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Expected Recovery Assertion
            </label>
            <textarea
              rows={2}
              value={expectedRecovery}
              onChange={(e) => setExpectedRecovery(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Automated Abort Conditions
            </label>
            <input
              type="text"
              value={abortConditions}
              onChange={(e) => setAbortConditions(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 focus:ring-1 focus:ring-indigo-500 font-mono"
            />
          </div>

          <div className="p-3 bg-slate-950 rounded border border-slate-800 text-[11px] text-slate-400">
            Safety Guardrail: Production exercises are blocked by default. Simulations run non-destructive verification without modifying live customer state.
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-semibold shadow-sm transition disabled:opacity-50"
            >
              {isLoading ? "Creating..." : "Create Planned Drill"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

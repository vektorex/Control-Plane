"use client";

import React, { useState } from "react";
import {
  FlaskConical,
  X,
  AlertTriangle,
  Shield,
  CheckCircle,
} from "lucide-react";
import { reliabilityService } from "@/services/reliability";

const ALLOWED_FAILURES = [
  { value: "simulate_timeout", label: "Simulate Timeout", defaultTarget: "ai_gateway" },
  { value: "simulate_provider_unavailable", label: "Simulate AI Provider Outage", defaultTarget: "ai_gateway" },
  { value: "simulate_rate_limit", label: "Simulate HTTP 429 Rate Limit", defaultTarget: "ai_gateway" },
  { value: "simulate_connector_failure", label: "Simulate Connector Failure", defaultTarget: "connector" },
  { value: "simulate_tool_failure", label: "Simulate Tool Execution Failure", defaultTarget: "tool" },
  { value: "simulate_cache_unavailable", label: "Simulate Semantic Cache Outage", defaultTarget: "cache" },
  { value: "simulate_event_delay", label: "Simulate Event Bus Delay", defaultTarget: "event_bus" },
  { value: "simulate_job_failure", label: "Simulate Worker Crash / Lease Expiry", defaultTarget: "worker" },
  { value: "simulate_notification_failure", label: "Simulate Notification Delivery Failure", defaultTarget: "notification" },
  { value: "simulate_retrieval_failure", label: "Simulate Vector Retrieval Failure", defaultTarget: "retrieval" },
  { value: "simulate_evaluation_failure", label: "Simulate Evaluator Timeout", defaultTarget: "evaluation" },
];

export function ChaosExperimentModal({ isOpen, onClose, onSuccess }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [environment, setEnvironment] = useState("test");
  const [failureType, setFailureType] = useState("simulate_timeout");
  const [targetType, setTargetType] = useState("ai_gateway");
  const [targetId, setTargetId] = useState("openai_primary");
  const [durationSeconds, setDurationSeconds] = useState(30);
  const [expectedBehavior, setExpectedBehavior] = useState("System triggers fallback model and retries within 5 seconds without user impact.");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  if (!isOpen) return null;

  const handleFailureChange = (e) => {
    const val = e.target.value;
    setFailureType(val);
    const item = ALLOWED_FAILURES.find((f) => f.value === val);
    if (item) {
      setTargetType(item.defaultTarget);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !targetId.trim() || !expectedBehavior.trim()) {
      setErrorMsg("All fields are required.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg("");

      const res = await reliabilityService.createExperiment({
        name: name.trim(),
        description: description.trim(),
        environment,
        target_type: targetType,
        target_id: targetId.trim(),
        failure_type: failureType,
        duration_seconds: parseInt(durationSeconds, 10),
        expected_behavior: expectedBehavior.trim(),
        abort_conditions: {
          abort_on_error_rate_exceeding: 0.25,
          abort_on_unhandled_exception: True,
        },
      });

      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Failed to create chaos experiment.");
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
          <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/40 text-purple-400">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Create Chaos Experiment</h3>
            <p className="text-xs text-slate-500">
              Safe, allowlisted failure injection strictly isolated to test and sandbox environments.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Experiment Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. AI Gateway Provider Outage Fallback Test"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              required
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Description / Hypothesis</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What resilience assumption does this experiment validate?"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white placeholder-slate-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Environment</label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
              >
                <option value="test">Test</option>
                <option value="sandbox">Sandbox</option>
                <option value="staging">Staging</option>
                <option value="production">Production (Requires HITL + Governance)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Duration (seconds)</label>
              <input
                type="number"
                min={5}
                max={300}
                value={durationSeconds}
                onChange={(e) => setDurationSeconds(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Failure Injection Mode</label>
            <select
              value={failureType}
              onChange={handleFailureChange}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white font-mono"
            >
              {ALLOWED_FAILURES.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label} ({f.value})
                </option>
              ))}
            </select>
          </div>

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
                placeholder="e.g. openai_primary or connector_github"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white font-mono"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Expected System Behavior</label>
            <textarea
              rows={2}
              value={expectedBehavior}
              onChange={(e) => setExpectedBehavior(e.target.value)}
              placeholder="e.g. Circuit opens, fallback activates, workflow pauses without data corruption..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white"
              required
            />
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
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Save Experiment"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

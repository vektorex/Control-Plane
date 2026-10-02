"use client";

import React, { useState } from "react";
import {
  X,
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Code2,
  Sliders,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { triggerService } from "@/services/triggers";

export function TriggerTestModal({ trigger, isOpen, onClose }) {
  if (!isOpen || !trigger) return null;

  const defaultSample =
    trigger.trigger_type === "connector_event" || trigger.name.toLowerCase().includes("github")
      ? {
          action: "opened",
          issue: {
            number: 42,
            title: "Fix broken auth token refresh",
            labels: ["bug", "security"],
            state: "open",
          },
          repository: {
            full_name: "org/core-repo",
            name: "core-repo",
          },
        }
      : {
          event: "payment_succeeded",
          amount: 250,
          currency: "usd",
          customer: { id: "cus_123", email: "user@example.com" },
          env: "production",
        };

  const [payloadText, setPayloadText] = useState(JSON.stringify(defaultSample, null, 2));
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRunTest = async () => {
    try {
      setTesting(true);
      setError(null);
      setTestResult(null);

      let parsed = {};
      try {
        parsed = JSON.parse(payloadText);
      } catch (err) {
        throw new Error("Invalid JSON in sample payload.");
      }

      const result = await triggerService.testTrigger(trigger.id, {
        sample_payload: parsed,
      });
      setTestResult(result);
    } catch (err) {
      console.error("[TriggerTest] Error:", err);
      setError(err.message || "Failed to execute dry-run test.");
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            <div>
              <h2 className="text-sm font-semibold text-slate-100">
                Dry-Run Trigger Test: {trigger.name}
              </h2>
              <p className="text-[11px] text-slate-400">
                Evaluates filters and payload variable mapping without side effects.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4 text-xs">
          {error && (
            <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-rose-300">
              {error}
            </div>
          )}

          <div>
            <label className="mb-1.5 block font-semibold text-slate-300">
              Sample Event Payload (JSON)
            </label>
            <textarea
              rows={8}
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              className="w-full font-mono rounded-lg border border-slate-800 bg-slate-950 p-3 text-[11px] text-indigo-300 placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {testResult && (
            <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">Evaluation Outcome:</span>
                {testResult.filter_matched ? (
                  <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Filters Matched (Accepted)
                  </Badge>
                ) : (
                  <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/30 gap-1">
                    <XCircle className="h-3 w-3" />
                    Filter Mismatch (Suppressed)
                  </Badge>
                )}
              </div>

              {/* Rule Breakdown */}
              {testResult.filter_details?.rule_results?.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-slate-400">Rules Breakdown:</span>
                  <div className="space-y-1 rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                    {testResult.filter_details.rule_results.map((r, i) => (
                      <div key={i} className="flex items-center justify-between text-[11px]">
                        <span className="font-mono text-slate-300">
                          {r.field} {r.operator} &quot;{String(r.expected)}&quot;
                        </span>
                        {r.passed ? (
                          <span className="font-semibold text-emerald-400">PASSED (actual: &quot;{String(r.actual)}&quot;)</span>
                        ) : (
                          <span className="font-semibold text-rose-400">FAILED (actual: &quot;{String(r.actual)}&quot;)</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Mapped Inputs */}
              <div>
                <span className="text-[11px] font-semibold text-slate-400">
                  Resolved Workflow Inputs:
                </span>
                <pre className="mt-1 overflow-x-auto rounded-lg border border-slate-800 bg-slate-900 p-2.5 font-mono text-[11px] text-emerald-300">
                  {JSON.stringify(testResult.mapped_inputs, null, 2)}
                </pre>
              </div>

              {/* Warnings */}
              {testResult.policy_warnings?.length > 0 && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5 text-amber-300">
                  <div className="flex items-center gap-1.5 font-semibold text-[11px]">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Policy Warnings:
                  </div>
                  <ul className="mt-1 list-inside list-disc space-y-0.5 text-[11px]">
                    {testResult.policy_warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-slate-800 px-6 py-3">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRunTest}
            disabled={testing}
            className="gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            {testing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            Run Dry-Run Test
          </Button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  FlaskConical,
  ShieldAlert,
  Play,
  CheckCircle,
  Square,
  Clock,
  AlertTriangle,
  RefreshCw,
  Terminal,
  Activity,
  Layers,
  FileCheck,
} from "lucide-react";
import { reliabilityService } from "@/services/reliability";

export default function ChaosExperimentDetailPage({ params }) {
  const unwrappedParams = use(params);
  const experimentId = unwrappedParams.experimentId;

  const [experiment, setExperiment] = useState(null);
  const [safetySummary, setSafetySummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");

      const [expRes, safeRes] = await Promise.allSettled([
        reliabilityService.getExperiment(experimentId),
        reliabilityService.getExperimentSafetySummary(experimentId),
      ]);

      if (expRes.status === "fulfilled") {
        setExperiment(expRes.value);
      } else {
        throw new Error("Experiment not found.");
      }

      if (safeRes.status === "fulfilled") {
        setSafetySummary(safeRes.value);
      }
    } catch (err) {
      setErrorMsg(err.message || "Failed to load experiment details.");
    } finally {
      setIsLoading(false);
    }
  }, [experimentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApprove = async () => {
    try {
      setActionLoading(true);
      await reliabilityService.approveExperiment(experimentId);
      await fetchData();
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRun = async () => {
    try {
      setActionLoading(true);
      await reliabilityService.runExperiment(experimentId);
      await fetchData();
    } catch (err) {
      alert(`Run error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAbort = async () => {
    try {
      setActionLoading(true);
      await reliabilityService.abortExperiment(experimentId, "Manual emergency abort by operator");
      await fetchData();
    } catch (err) {
      alert(`Abort error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading && !experiment) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
        Loading chaos experiment...
      </div>
    );
  }

  if (errorMsg || !experiment) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/app/reliability/experiments"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Experiments
        </Link>
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-200 text-sm">
          {errorMsg || "Experiment not found."}
        </div>
      </div>
    );
  }

  const isProduction = experiment.environment === "production";
  const observations = experiment.observations || [];
  const runs = experiment.runs || [];

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/app/reliability/experiments"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Experiments
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl">
              <FlaskConical className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  {experiment.name}
                </h1>
                <span
                  className={`text-xs uppercase font-mono font-bold px-2 py-0.5 rounded border ${
                    isProduction
                      ? "bg-red-950 text-red-400 border-red-800"
                      : "bg-blue-950 text-blue-400 border-blue-800"
                  }`}
                >
                  {experiment.environment}
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {experiment.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {experiment.description || "Controlled synthetic resilience experiment"}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {experiment.status === "planned" && (
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <CheckCircle className="w-3.5 h-3.5" /> Approve
              </button>
            )}

            {experiment.status === "approved" && (
              <button
                onClick={handleRun}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" /> Execute Run
              </button>
            )}

            {(experiment.status === "running" || experiment.status === "approved") && (
              <button
                onClick={handleAbort}
                disabled={actionLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <Square className="w-3.5 h-3.5" /> Abort
              </button>
            )}

            <button
              onClick={fetchData}
              disabled={isLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Safety Blast Radius Card */}
      {safetySummary && (
        <div
          className={`p-4 rounded-xl border ${
            safetySummary.production_blocked
              ? "bg-amber-950/20 border-amber-800/60"
              : "bg-slate-900 border-slate-800"
          }`}
        >
          <div className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            Safety & Blast Radius Summary
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono mt-3">
            <div>
              <span className="text-slate-500 block">Target Scope</span>
              <span className="text-white font-semibold">
                {safetySummary.target_type}: {safetySummary.target_id}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Failure Injection</span>
              <span className="text-amber-300 font-semibold">
                {safetySummary.failure_type}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Injection Duration</span>
              <span className="text-white">{safetySummary.duration_seconds} seconds</span>
            </div>
            <div>
              <span className="text-slate-500 block">Approval Level</span>
              <span className="text-slate-300">{safetySummary.approval_requirement}</span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-400 flex items-start gap-2">
            <span className="text-slate-500 shrink-0 font-semibold">Blast Assessment:</span>
            <span>{safetySummary.blast_radius_assessment}</span>
          </div>
        </div>
      )}

      {/* Experiment Parameters */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-white">Experiment Specification</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1">
            <span className="text-slate-400">Expected Resilience Behavior:</span>
            <div className="p-3 bg-slate-950 rounded-lg text-slate-300 border border-slate-800 font-mono">
              {experiment.expected_behavior}
            </div>
          </div>
          <div className="space-y-1">
            <span className="text-slate-400">Automated Abort Conditions:</span>
            <div className="p-3 bg-slate-950 rounded-lg text-amber-300 border border-slate-800 font-mono">
              {experiment.abort_conditions || "Abort on error rate > 5% or lease expiration"}
            </div>
          </div>
        </div>
      </div>

      {/* Observations Stream */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Observations & Telemetry Log</h3>
          </div>
          <span className="text-xs text-slate-500">{observations.length} observations</span>
        </div>

        {observations.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs font-mono">
            No observations recorded yet. Run the experiment to verify fallback and recovery behavior.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Timestamp</th>
                  <th className="py-2.5 px-4 font-semibold">Observed Metric</th>
                  <th className="py-2.5 px-4 font-semibold">Value</th>
                  <th className="py-2.5 px-4 font-semibold">Expected</th>
                  <th className="py-2.5 px-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {observations.map((obs) => (
                  <tr key={obs.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-4 text-slate-400">
                      {new Date(obs.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-4 font-semibold text-white">
                      {obs.metric}
                    </td>
                    <td className="py-2.5 px-4 text-indigo-300">
                      {obs.value}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400">
                      {obs.expected_value || "-"}
                    </td>
                    <td className="py-2.5 px-4">
                      {obs.status === "passed" ? (
                        <span className="text-emerald-400 font-bold">PASSED</span>
                      ) : (
                        <span className="text-amber-400 font-bold">{obs.status.toUpperCase()}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="text-[11px] text-slate-500 text-center font-mono">
        Disclaimer: Results demonstrate resilience under specific synthetic injection parameters only; they do not constitute a universal uptime guarantee.
      </div>
    </div>
  );
}

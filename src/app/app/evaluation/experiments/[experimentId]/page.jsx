"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  PlayCircle,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Coins,
  Cpu,
  RefreshCw,
  GitCompare,
  ArrowRight,
  ShieldCheck,
  StopCircle,
  Eye,
  FileCode,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function ExperimentResultsPage() {
  const params = useParams();
  const experimentId = params?.experimentId;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (experimentId) {
      loadResults();
    }
  }, [experimentId]);

  async function loadResults() {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluationLabService.getExperimentResults(experimentId);
      setData(res);
    } catch (err) {
      setError(err?.message || "Failed to load experiment results");
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel() {
    if (!confirm("Are you sure you want to stop this experiment?")) return;
    setCancelling(true);
    try {
      await evaluationLabService.cancelExperiment(experimentId);
      await loadResults();
    } catch (err) {
      alert(err?.message || "Failed to cancel experiment");
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
        <RefreshCw className="w-6 h-6 animate-spin text-primary" />
        Loading experiment execution results...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center space-y-4">
        <p className="text-red-500">{error || "Experiment not found"}</p>
        <Link href="/app/evaluation" className="text-xs text-primary hover:underline">
          Return to Evaluation Hub
        </Link>
      </div>
    );
  }

  const { experiment, summary, runs } = data;
  const isRunning = experiment.status === "running" || experiment.status === "queued";

  const filteredRuns = runs.filter((r) =>
    statusFilter === "all" ? true : r.status === statusFilter
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            <Link href="/app/evaluation" className="hover:text-foreground">Evaluation Lab</Link>
            <span>/</span>
            <span>Experiments</span>
            <span>/</span>
            <span>{experiment.name}</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <PlayCircle className="w-6 h-6 text-purple-500" />
              {experiment.name}
            </h1>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                experiment.status === "completed"
                  ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                  : experiment.status === "running"
                  ? "bg-blue-500/10 text-blue-500 border border-blue-500/20 animate-pulse"
                  : experiment.status === "failed"
                  ? "bg-red-500/10 text-red-500 border border-red-500/20"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {experiment.status}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
            <span>Target: <strong className="text-foreground capitalize">{experiment.target_type}</strong></span>
            {experiment.target_configuration?.model && (
              <>
                <span>•</span>
                <span>Model: <strong className="text-foreground">{experiment.target_configuration.model}</strong></span>
              </>
            )}
            {experiment.completed_at && (
              <>
                <span>•</span>
                <span>Completed: {new Date(experiment.completed_at).toLocaleString()}</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isRunning && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="px-3.5 py-1.5 text-xs font-medium rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500/10 transition flex items-center gap-1.5"
            >
              <StopCircle className="w-3.5 h-3.5" />
              {cancelling ? "Stopping..." : "Cancel Experiment"}
            </button>
          )}

          <Link
            href={`/app/evaluation/compare?experiment_a=${experiment.id}`}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-accent/40 text-foreground transition flex items-center gap-1.5"
          >
            <GitCompare className="w-3.5 h-3.5 text-muted-foreground" />
            Compare
          </Link>

          <Link
            href={`/app/evaluation/regressions?baseline=${experiment.id}`}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-accent/40 text-foreground transition flex items-center gap-1.5"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            Check Regressions
          </Link>

          <button
            onClick={loadResults}
            className="p-1.5 rounded-lg border border-border/60 hover:bg-accent/40 text-muted-foreground transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase">Total Cases</span>
          <p className="text-xl font-bold text-foreground font-mono">{summary.total_cases}</p>
        </div>

        <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-1">
          <span className="text-[11px] font-semibold text-emerald-500 uppercase">Passed</span>
          <p className="text-xl font-bold text-emerald-500 font-mono">{summary.passed}</p>
        </div>

        <div className="p-3.5 rounded-xl border border-red-500/20 bg-red-500/5 space-y-1">
          <span className="text-[11px] font-semibold text-red-500 uppercase">Failed</span>
          <p className="text-xl font-bold text-red-500 font-mono">{summary.failed}</p>
        </div>

        <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
            <Clock className="w-3 h-3" /> Avg Latency
          </span>
          <p className="text-xl font-bold text-foreground font-mono">{summary.average_latency_ms} ms</p>
        </div>

        <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
            <Cpu className="w-3 h-3" /> Tokens
          </span>
          <p className="text-xl font-bold text-foreground font-mono">{summary.total_tokens}</p>
        </div>

        <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
            <Coins className="w-3 h-3" /> Cost ($)
          </span>
          <p className="text-xl font-bold text-foreground font-mono">${summary.estimated_cost}</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border/40 pb-2">
        {["all", "passed", "failed", "warning", "error"].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1 text-xs font-medium rounded-lg capitalize transition ${
              statusFilter === st
                ? "bg-primary text-primary-foreground font-semibold"
                : "text-muted-foreground hover:bg-accent/40 hover:text-foreground"
            }`}
          >
            {st} ({st === "all" ? runs.length : runs.filter((r) => r.status === st).length})
          </button>
        ))}
      </div>

      {/* Cases Table */}
      <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/40 border-b border-border/40 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
              <tr>
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Assertions Passed</th>
                <th className="py-3 px-4">Verification Findings</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Tokens</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {filteredRuns.map((r) => {
                const asserts = r.evaluation_result?.assertions || [];
                const passedAsserts = asserts.filter((a) => a.passed).length;
                const findings = r.evaluation_result?.evaluation_findings || [];

                return (
                  <tr key={r.id} className="hover:bg-accent/20 transition">
                    <td className="py-3 px-4 font-mono text-xs text-foreground">
                      {r.case_id.substring(0, 8)}...
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          r.status === "passed"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : r.status === "failed"
                            ? "bg-red-500/10 text-red-500"
                            : r.status === "warning"
                            ? "bg-amber-500/10 text-amber-500"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs font-mono">
                      {passedAsserts} / {asserts.length} passed
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {findings.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {findings.map((f, i) => (
                            <span
                              key={i}
                              className={`text-[10px] px-1.5 py-0.5 rounded ${
                                f.passed
                                  ? "bg-emerald-500/10 text-emerald-500"
                                  : "bg-red-500/10 text-red-500 font-bold"
                              }`}
                            >
                              {f.check_type}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground font-mono">
                      {r.latency_ms || 0} ms
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground font-mono">
                      {(r.input_tokens || 0) + (r.output_tokens || 0)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        href={`/app/evaluation/experiments/${experiment.id}/cases/${r.case_id}`}
                        className="px-2.5 py-1 text-xs font-medium rounded border border-border/60 hover:bg-accent text-foreground transition inline-flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3 text-muted-foreground" />
                        Inspect
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

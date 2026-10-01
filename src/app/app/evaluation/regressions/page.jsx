"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Coins,
  ArrowRight,
  RefreshCw,
  Eye,
  RotateCcw,
  ShieldAlert,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function RegressionsDashboardPage() {
  const searchParams = useSearchParams();
  const initialBase = searchParams.get("baseline") || "";
  const initialCand = searchParams.get("candidate") || "";

  const [experiments, setExperiments] = useState([]);
  const [baselineId, setBaselineId] = useState(initialBase);
  const [candidateId, setCandidateId] = useState(initialCand);

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadExperiments();
  }, []);

  useEffect(() => {
    if (baselineId && candidateId && baselineId !== candidateId) {
      checkRegressions(baselineId, candidateId);
    }
  }, [baselineId, candidateId]);

  async function loadExperiments() {
    try {
      const res = await evaluationLabService.listExperiments({ limit: 100 });
      const items = res?.items || [];
      setExperiments(items);
      if (!baselineId && items.length > 0) setBaselineId(items[0].id);
      if (!candidateId && items.length > 1) setCandidateId(items[1].id);
    } catch (err) {
      console.error(err);
    }
  }

  async function checkRegressions(base, cand) {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluationLabService.checkRegressions(base, cand);
      setReport(res);
    } catch (err) {
      setError(err?.message || "Failed to check regressions");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="border-b border-border/40 pb-5">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
          <Link href="/app/evaluation" className="hover:text-foreground">Evaluation Lab</Link>
          <span>/</span>
          <span>Regressions</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-amber-500" />
          Continuous Regression Dashboard
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Deterministic detection of lost citations, grounding failures, latency spikes, and cost increases.
        </p>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Baseline Experiment
          </label>
          <select
            value={baselineId}
            onChange={(e) => setBaselineId(e.target.value)}
            className="w-full mt-1.5 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">Select Baseline...</option>
            {experiments.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.target_type} - {e.target_configuration?.model || "custom"})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Candidate Experiment
          </label>
          <select
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            className="w-full mt-1.5 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">Select Candidate...</option>
            {experiments.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.target_type} - {e.target_configuration?.model || "custom"})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-primary" />
          Checking regressions against deterministic thresholds...
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-xs text-red-500">
          {error}
        </div>
      ) : !report ? (
        <div className="py-16 text-center text-sm text-muted-foreground">
          Select baseline and candidate experiments above to analyze regressions.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Status Banner */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${
              report.regression_detected
                ? "border-amber-500/30 bg-amber-500/10 text-amber-500"
                : "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
            }`}
          >
            <div className="flex items-center gap-3">
              {report.regression_detected ? (
                <ShieldAlert className="w-6 h-6 shrink-0" />
              ) : (
                <CheckCircle2 className="w-6 h-6 shrink-0" />
              )}
              <div>
                <h3 className="font-bold text-sm">
                  {report.regression_detected
                    ? `${report.regressions.length} Regression(s) Detected`
                    : "No Regressions Detected"}
                </h3>
                <p className="text-xs opacity-90 mt-0.5">
                  {report.regression_detected
                    ? "Candidate experiment triggered diagnostic threshold breaches or lost verification checks."
                    : "All deterministic checks passed consistently and operational deltas are within bounds."}
                </p>
              </div>
            </div>

            <div className="text-right text-xs font-mono">
              Thresholds: 5% fail rate, 25% latency, 25% cost
            </div>
          </div>

          {/* Metric Threshold Deltas */}
          {report.metrics_deltas && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
                <span className="text-[11px] font-semibold text-muted-foreground uppercase">
                  Failure Rate Delta
                </span>
                <p className="text-xl font-bold text-foreground font-mono">
                  {report.metrics_deltas.failure_rate_delta > 0 ? "+" : ""}
                  {roundPct(report.metrics_deltas.failure_rate_delta)}%
                </p>
                <p className="text-xs text-muted-foreground">
                  Limit: 5% increase max
                </p>
              </div>

              <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
                <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> Latency Increase
                </span>
                <p className="text-xl font-bold text-foreground font-mono">
                  {report.metrics_deltas.latency_pct_increase > 0 ? "+" : ""}
                  {report.metrics_deltas.latency_pct_increase}%
                </p>
                <p className="text-xs text-muted-foreground">
                  Limit: 25% increase max
                </p>
              </div>

              <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
                <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
                  <Coins className="w-3.5 h-3.5" /> Cost Increase
                </span>
                <p className="text-xl font-bold text-foreground font-mono">
                  {report.metrics_deltas.cost_pct_increase > 0 ? "+" : ""}
                  {report.metrics_deltas.cost_pct_increase}%
                </p>
                <p className="text-xs text-muted-foreground">
                  Limit: 25% increase max
                </p>
              </div>
            </div>
          )}

          {/* Regressions List */}
          <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
            <div className="p-4 border-b border-border/40">
              <h3 className="text-sm font-semibold text-foreground">
                Regression Findings ({report.regressions.length})
              </h3>
            </div>

            {report.regressions.length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground">
                No regressions detected between selected baseline and candidate runs.
              </div>
            ) : (
              <div className="divide-y divide-border/30">
                {report.regressions.map((reg, idx) => (
                  <div key={idx} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-foreground">{reg.case_key}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 font-mono">
                          {reg.check}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">{reg.reason}</p>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-xs font-mono">
                        <span className="text-emerald-500">{String(reg.baseline_result)}</span>
                        <span className="mx-2 text-muted-foreground">→</span>
                        <span className="text-red-500 font-bold">{String(reg.candidate_result)}</span>
                      </div>

                      {reg.case_id !== "aggregate" && (
                        <Link
                          href={`/app/evaluation/experiments/${candidateId}/cases/${reg.case_id}`}
                          className="px-2.5 py-1 text-xs font-medium rounded border border-border/60 hover:bg-accent text-foreground transition inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3 text-muted-foreground" />
                          Inspect
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function roundPct(val) {
  if (val === undefined || val === null) return 0;
  return Math.round(val * 1000) / 10;
}

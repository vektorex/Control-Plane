"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  GitCompare,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Cpu,
  Coins,
  ShieldCheck,
  FileCode,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function CompareExperimentsPage() {
  const searchParams = useSearchParams();
  const initialA = searchParams.get("experiment_a") || "";
  const initialB = searchParams.get("experiment_b") || "";

  const [experiments, setExperiments] = useState([]);
  const [selectedA, setSelectedA] = useState(initialA);
  const [selectedB, setSelectedB] = useState(initialB);

  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadExperiments();
  }, []);

  useEffect(() => {
    if (selectedA && selectedB && selectedA !== selectedB) {
      runComparison(selectedA, selectedB);
    }
  }, [selectedA, selectedB]);

  async function loadExperiments() {
    try {
      const res = await evaluationLabService.listExperiments({ limit: 100 });
      const items = res?.items || [];
      setExperiments(items);
      if (!selectedA && items.length > 0) setSelectedA(items[0].id);
      if (!selectedB && items.length > 1) setSelectedB(items[1].id);
    } catch (err) {
      console.error(err);
    }
  }

  async function runComparison(idA, idB) {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluationLabService.compareExperiments(idA, idB);
      setComparison(res);
    } catch (err) {
      setError(err?.message || "Failed to compare experiments");
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
          <span>Comparison</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <GitCompare className="w-6 h-6 text-emerald-500" />
          Factual Experiment Comparison
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Side-by-side empirical differential analysis of cases, assertions, latency, and tokens.
        </p>
      </div>

      {/* Experiment Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm">
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Baseline Experiment (A)
          </label>
          <select
            value={selectedA}
            onChange={(e) => setSelectedA(e.target.value)}
            className="w-full mt-1.5 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">Select Experiment A...</option>
            {experiments.map((e) => (
              <option key={e.id} value={e.id}>
                {e.name} ({e.target_type} - {e.target_configuration?.model || "custom"})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Candidate Experiment (B)
          </label>
          <select
            value={selectedB}
            onChange={(e) => setSelectedB(e.target.value)}
            className="w-full mt-1.5 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">Select Experiment B...</option>
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
          Computing factual differential report...
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-xs text-red-500">
          {error}
        </div>
      ) : !comparison ? (
        <div className="py-16 text-center text-sm text-muted-foreground">
          Select two experiments above to view their factual execution differences.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Metric Deltas */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase">Case Differences</span>
              <p className="text-2xl font-bold text-foreground font-mono">
                {comparison.summary.cases_difference}
              </p>
              <p className="text-xs text-muted-foreground">Status changed between A and B</p>
            </div>

            <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase">Assertion Deltas</span>
              <p className="text-2xl font-bold text-foreground font-mono">
                {comparison.summary.assertions_difference}
              </p>
              <p className="text-xs text-muted-foreground">Rules with divergent outcomes</p>
            </div>

            <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase">Avg Latency Delta</span>
              <p className="text-2xl font-bold text-foreground font-mono">
                {comparison.latency_difference.delta_ms > 0 ? "+" : ""}
                {comparison.latency_difference.delta_ms} ms
              </p>
              <p className="text-xs text-muted-foreground">
                {comparison.latency_difference.baseline_avg_ms} ms → {comparison.latency_difference.candidate_avg_ms} ms
              </p>
            </div>

            <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase">Estimated Cost Delta</span>
              <p className="text-2xl font-bold text-foreground font-mono">
                {comparison.cost_difference.delta_cost > 0 ? "+" : ""}
                ${comparison.cost_difference.delta_cost}
              </p>
              <p className="text-xs text-muted-foreground">
                ${comparison.cost_difference.baseline_cost} → ${comparison.cost_difference.candidate_cost}
              </p>
            </div>
          </div>

          {/* Factual Disclaimer */}
          <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-xs text-muted-foreground flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>
              <strong>Factual Differential Guarantee:</strong> This report presents empirical changes in status, latency, and tokens. Models are not ranked, and no subjective "winner" scores are computed.
            </span>
          </div>

          {/* Regressions Section */}
          {comparison.regressions && comparison.regressions.length > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 overflow-hidden">
              <div className="p-4 border-b border-amber-500/20 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-amber-500 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Detected Status Regressions ({comparison.regressions.length})
                </h3>
              </div>
              <div className="divide-y divide-amber-500/10">
                {comparison.regressions.map((reg, idx) => (
                  <div key={idx} className="p-4 flex items-center justify-between gap-4">
                    <div>
                      <span className="font-mono text-xs font-bold text-foreground">{reg.case_key}</span>
                      <p className="text-xs text-muted-foreground mt-0.5">{reg.reason}</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className="text-emerald-500">{reg.baseline_result}</span>
                      <ArrowRight className="w-3 h-3 text-muted-foreground" />
                      <span className="text-red-500 font-bold">{reg.candidate_result}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Case Differences Table */}
          <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
            <div className="p-4 border-b border-border/40">
              <h3 className="text-sm font-semibold text-foreground">
                Case Status Divergences ({comparison.case_differences.length})
              </h3>
            </div>

            {comparison.case_differences.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                All cases produced identical pass/fail statuses across both experiments.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted/40 border-b border-border/40 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                    <tr>
                      <th className="py-3 px-4">Case Key</th>
                      <th className="py-3 px-4">Name</th>
                      <th className="py-3 px-4">Experiment A Status</th>
                      <th className="py-3 px-4">Experiment B Status</th>
                      <th className="py-3 px-4">Latency Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/30">
                    {comparison.case_differences.map((cd, idx) => (
                      <tr key={idx} className="hover:bg-accent/20 transition">
                        <td className="py-3 px-4 font-mono text-xs text-foreground font-medium">
                          {cd.case_key}
                        </td>
                        <td className="py-3 px-4 text-xs text-muted-foreground">{cd.case_name}</td>
                        <td className="py-3 px-4 text-xs font-medium capitalize text-foreground">
                          {cd.status_a}
                        </td>
                        <td className="py-3 px-4 text-xs font-medium capitalize text-foreground">
                          {cd.status_b}
                        </td>
                        <td className="py-3 px-4 text-xs font-mono text-muted-foreground">
                          {cd.latency_a_ms && cd.latency_b_ms
                            ? `${cd.latency_b_ms - cd.latency_a_ms > 0 ? "+" : ""}${
                                cd.latency_b_ms - cd.latency_a_ms
                              } ms`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Assertion Differences */}
          <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
            <div className="p-4 border-b border-border/40">
              <h3 className="text-sm font-semibold text-foreground">
                Assertion Outcomes Divergences ({comparison.assertion_differences.length})
              </h3>
            </div>

            {comparison.assertion_differences.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                All deterministic assertions had identical outcomes in both experiments.
              </div>
            ) : (
              <div className="divide-y divide-border/30">
                {comparison.assertion_differences.map((ad, idx) => (
                  <div key={idx} className="p-4 flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-foreground">{ad.case_key}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground font-mono">
                          {ad.assertion_type}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">{ad.message_b || ad.message_a}</p>
                    </div>

                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span>Exp A: {ad.passed_a ? "Passed" : "Failed"}</span>
                      <ArrowRight className="w-3 h-3 text-muted-foreground" />
                      <span>Exp B: {ad.passed_b ? "Passed" : "Failed"}</span>
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

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { SideEffectPreviewPanel } from "@/components/simulation/SideEffectPreviewPanel";
import { AssertionResultsTable } from "@/components/simulation/AssertionResultsTable";
import { simulationService } from "@/services/simulation";
import {
  FlaskConical,
  ArrowLeft,
  RefreshCw,
  GitCompare,
  FileText,
  Clock,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Eye,
} from "lucide-react";

export default function SimulationRunsPage() {
  const params = useParams();
  const simulationId = params?.simulationId;

  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [compareTargetRunId, setCompareTargetRunId] = useState("");
  const [error, setError] = useState(null);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await simulationService.listSimulationRuns(simulationId, { limit: 50 });
      setRuns(data || []);
      if (data && data.length > 0) {
        setSelectedRun(data[0]);
      }
    } catch (err) {
      console.error("[SimulationRunsPage] Error:", err);
      setError(err.message || "Failed to load runs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (simulationId) fetchRuns();
  }, [simulationId]);

  const handleSelectRun = async (runId) => {
    try {
      const full = await simulationService.getRun(runId);
      setSelectedRun(full);
      setComparisonResult(null);
    } catch (err) {
      console.error("[SimulationRunsPage] Error getting run:", err);
    }
  };

  const handleCompare = async () => {
    if (!selectedRun || !compareTargetRunId) return;
    try {
      setError(null);
      const res = await simulationService.compareRuns(selectedRun.id, compareTargetRunId);
      setComparisonResult(res.factual_differences);
    } catch (err) {
      console.error("[SimulationRunsPage] Compare error:", err);
      setError(err.message || "Failed to compute factual comparison.");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <Link
        href={`/app/simulations/${simulationId}`}
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Simulation Overview
      </Link>

      <SimulationBanner mode="ISOLATED" seed={selectedRun?.seed || 42} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-400" />
            Simulation Run History & Comparison
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Review deterministic trace outputs, intercepted actions, and compare runs factually.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={fetchRuns} className="border-zinc-700 text-zinc-300">
          <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> Refresh
        </Button>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs">
          {error}
        </div>
      )}

      {/* Runs Table */}
      <Card className="border-zinc-800 bg-zinc-900/80 overflow-hidden">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
            Execution Runs ({runs.length})
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-950/80 text-zinc-400">
                <th className="p-3">Run ID</th>
                <th className="p-3">Status</th>
                <th className="p-3">Seed</th>
                <th className="p-3">Side Effects</th>
                <th className="p-3">Assertions</th>
                <th className="p-3">Latency</th>
                <th className="p-3">Cost</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {runs.map((r) => {
                const passed = (r.assertion_results || []).filter((a) => a.passed).length;
                const total = (r.assertion_results || []).length;
                const isSelected = selectedRun?.id === r.id;

                return (
                  <tr
                    key={r.id}
                    onClick={() => handleSelectRun(r.id)}
                    className={`cursor-pointer transition ${
                      isSelected ? "bg-amber-950/30 font-medium" : "hover:bg-zinc-800/40"
                    }`}
                  >
                    <td className="p-3 font-mono text-zinc-300">{r.id.slice(0, 8)}...</td>
                    <td className="p-3">
                      <Badge
                        variant="outline"
                        className={
                          r.status === "completed"
                            ? "border-emerald-500/30 text-emerald-300 bg-emerald-950/20 text-[10px]"
                            : "border-red-500/30 text-red-300 bg-red-950/20 text-[10px]"
                        }
                      >
                        {r.status.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="p-3 font-mono text-amber-300">{r.seed}</td>
                    <td className="p-3">
                      <span className="text-zinc-300 font-medium">
                        {(r.side_effects || []).length} blocked
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={passed === total ? "text-emerald-400" : "text-amber-400"}>
                        {passed}/{total} passed
                      </span>
                    </td>
                    <td className="p-3 text-zinc-400">{r.latency}s</td>
                    <td className="p-3 text-zinc-400">${r.cost.toFixed(4)}</td>
                    <td className="p-3 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectRun(r.id);
                        }}
                        className="h-6 text-[11px] text-zinc-300 hover:text-white"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" /> View
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Selected Run Deep Dive & Compare Tool */}
      {selectedRun && (
        <div className="space-y-6">
          {/* Factual Comparison Panel */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <GitCompare className="w-4 h-4 text-purple-400" />
                  Factual Run Comparator
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Compare Run <span className="font-mono text-zinc-200">{selectedRun.id.slice(0, 8)}...</span> against another run. Identifies objective differences without subjective scoring.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={compareTargetRunId}
                  onChange={(e) => setCompareTargetRunId(e.target.value)}
                  className="bg-zinc-950 border border-zinc-800 text-xs rounded-md px-3 py-1.5 text-zinc-200"
                >
                  <option value="">Select comparison run...</option>
                  {runs
                    .filter((r) => r.id !== selectedRun.id)
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        Run {r.id.slice(0, 8)} (Seed: {r.seed}, {r.status})
                      </option>
                    ))}
                </select>
                <Button
                  size="sm"
                  onClick={handleCompare}
                  disabled={!compareTargetRunId}
                  className="bg-purple-600 hover:bg-purple-500 text-white text-xs"
                >
                  Compare
                </Button>
              </div>
            </div>

            {comparisonResult && (
              <div className="p-4 rounded-lg bg-zinc-950 border border-purple-500/30 space-y-3">
                <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-wider">
                  Factual Differences Identified:
                </h4>
                {comparisonResult.factual_differences?.length === 0 ? (
                  <p className="text-xs text-zinc-400">Both runs behaved identically under these parameters.</p>
                ) : (
                  <ul className="list-disc list-inside space-y-1 text-xs text-zinc-300">
                    {comparisonResult.factual_differences.map((diff, i) => (
                      <li key={i}>{diff}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </Card>

          {/* Intercepted Side Effects for Selected Run */}
          <SideEffectPreviewPanel sideEffects={selectedRun.side_effects || []} />

          {/* Assertions for Selected Run */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-3">
            <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Assertion Results
            </h3>
            <AssertionResultsTable assertions={selectedRun.assertion_results || []} />
          </Card>
        </div>
      )}
    </div>
  );
}

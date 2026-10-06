"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import {
  Boxes,
  ArrowLeft,
  Play,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Layers,
  ShieldAlert,
} from "lucide-react";

export default function SuiteDetailPage() {
  const params = useParams();
  const suiteId = params?.suiteId;

  const [suite, setSuite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [suiteRunResult, setSuiteRunResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchSuite = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await simulationService.getSuite(suiteId);
      setSuite(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to load suite.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (suiteId) fetchSuite();
  }, [suiteId]);

  const handleRunSuite = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await simulationService.runSuite(suiteId, { seed: 42 });
      setSuiteRunResult(res);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to execute suite.");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-zinc-400">Loading suite...</div>;
  }

  if (!suite) {
    return <div className="p-8 text-center text-zinc-400">Suite not found.</div>;
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <Link
        href="/app/simulations/suites"
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Suites
      </Link>

      <SimulationBanner mode="ISOLATED" seed={42} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5 rounded-lg bg-zinc-900 border border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {suite.target_type}
            </span>
            <h1 className="text-xl font-bold text-zinc-100">{suite.name}</h1>
          </div>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
            {suite.description || "Regression simulation suite battery."}
          </p>
          <div className="text-[11px] text-zinc-500 font-mono mt-2">
            Target ID: {suite.target_id}
          </div>
        </div>

        <Button
          onClick={handleRunSuite}
          disabled={running}
          className="bg-amber-600 hover:bg-amber-500 text-white font-medium flex items-center gap-1.5 shadow-md"
        >
          <Play className={`w-4 h-4 ${running ? "animate-spin" : ""}`} />
          {running ? "Executing Suite..." : "Run Regression Suite"}
        </Button>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs">
          {error}
        </div>
      )}

      {/* Execution Results */}
      {suiteRunResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Total Scenarios"
              value={suiteRunResult.total_scenarios}
              icon={Layers}
              description="Evaluated in battery"
            />
            <StatCard
              title="Passed Scenarios"
              value={suiteRunResult.completed_scenarios}
              icon={CheckCircle2}
              description="Zero assertion violations"
            />
            <StatCard
              title="Regressions Detected"
              value={suiteRunResult.regressions_detected?.length || 0}
              icon={AlertTriangle}
              description="Failed assertions or errors"
            />
          </div>

          {/* Regressions Detail */}
          {suiteRunResult.regressions_detected?.length > 0 && (
            <Card className="p-5 border-rose-500/30 bg-zinc-900/90 space-y-3">
              <h3 className="text-sm font-semibold text-rose-300 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Regressions Detected in Suite:
              </h3>
              <div className="space-y-2">
                {suiteRunResult.regressions_detected.map((reg, idx) => (
                  <div key={idx} className="p-3 rounded bg-zinc-950 border border-rose-950/50 text-xs">
                    <span className="font-semibold text-zinc-200">Scenario: {reg.scenario_name}</span>
                    <ul className="list-disc list-inside mt-1 text-rose-300 space-y-0.5">
                      {(reg.failed_assertions || []).map((fa, i) => (
                        <li key={i}>{fa.assertion_type}: {fa.details}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Runs list */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-3">
            <h3 className="text-sm font-semibold text-zinc-100">Scenario Run Outcomes</h3>
            <div className="space-y-2">
              {suiteRunResult.runs.map((r, i) => (
                <div key={r.id || i} className="p-3 rounded bg-zinc-950 border border-zinc-800 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    {r.status === "completed" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400" />
                    )}
                    <span className="font-mono text-zinc-200">Run {r.id.slice(0, 8)}</span>
                    <span className="text-zinc-500">Cost: ${r.cost.toFixed(4)}</span>
                  </div>
                  <Badge variant="outline" className="border-zinc-700 font-mono text-[10px]">
                    Latency: {r.latency}s
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Scenarios currently in suite */}
      <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-3">
        <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
          <Layers className="w-4 h-4 text-amber-400" />
          Scenarios Configured in this Suite ({suite.scenarios?.length || 0})
        </h3>
        {(!suite.scenarios || suite.scenarios.length === 0) ? (
          <p className="text-xs text-zinc-500">
            No scenarios directly attached yet. When run, all workspace scenarios targeting this agent/team are evaluated.
          </p>
        ) : (
          <div className="space-y-2">
            {suite.scenarios.map((sc, idx) => (
              <div key={idx} className="p-2.5 rounded bg-zinc-950 border border-zinc-800 text-xs font-mono text-zinc-300">
                Scenario ID: {sc.scenario_id}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

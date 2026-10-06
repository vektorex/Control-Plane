"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import {
  FlaskConical,
  ArrowLeft,
  Plus,
  Play,
  Layers,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";

export default function SimulationScenariosPage() {
  const params = useParams();
  const simulationId = params?.simulationId;

  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningScenarioId, setRunningScenarioId] = useState(null);
  const [lastRunResult, setLastRunResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchScenarios = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await simulationService.listScenarios();
      setScenarios(data || []);
    } catch (err) {
      console.error("[SimulationScenariosPage] Error:", err);
      setError(err.message || "Failed to load scenarios.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, [simulationId]);

  const handleRunScenario = async (scenarioId) => {
    try {
      setRunningScenarioId(scenarioId);
      setError(null);
      const run = await simulationService.runSimulation(simulationId, {
        scenario_id: scenarioId,
        seed: 42,
      });
      setLastRunResult(run);
    } catch (err) {
      console.error("[SimulationScenariosPage] Run error:", err);
      setError(err.message || "Failed to run scenario.");
    } finally {
      setRunningScenarioId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <Link
        href={`/app/simulations/${simulationId}`}
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Simulation
      </Link>

      <SimulationBanner mode="ISOLATED" seed={42} />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-amber-400" />
            Simulation Scenarios
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Test this simulation target against normal, edge-case, and adversarial scenarios.
          </p>
        </div>

        <Link href="/app/simulations/scenarios/new">
          <Button className="bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs flex items-center gap-1.5 shadow-md">
            <Plus className="w-4 h-4" /> New Custom Scenario
          </Button>
        </Link>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs">
          {error}
        </div>
      )}

      {lastRunResult && (
        <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Scenario executed successfully: Run ID <span className="font-mono">{lastRunResult.id.slice(0, 8)}...</span></span>
          </div>
          <Link href={`/app/simulations/${simulationId}/runs`}>
            <Button size="sm" variant="outline" className="h-6 text-[11px] border-emerald-500/40 text-emerald-300">
              Inspect in Runs
            </Button>
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {scenarios.map((scen) => (
          <Card key={scen.id} className="p-5 border-zinc-800 bg-zinc-900/80 hover:border-zinc-700 transition flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <Badge
                  variant="outline"
                  className={
                    scen.scenario_type === "adversarial" || scen.scenario_type === "security"
                      ? "border-red-500/40 text-red-300 bg-red-950/20 text-[10px]"
                      : "border-blue-500/40 text-blue-300 bg-blue-950/20 text-[10px]"
                  }
                >
                  {scen.scenario_type.toUpperCase()}
                </Badge>
                <span className="text-[11px] text-zinc-500 font-mono">
                  {(scen.assertions || []).length} assertions
                </span>
              </div>

              <h3 className="text-sm font-semibold text-zinc-100">{scen.name}</h3>
              <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
                {scen.description || "No description provided."}
              </p>

              <div className="mt-3 p-2 rounded bg-zinc-950 border border-zinc-800/80">
                <span className="text-[10px] text-zinc-500 block mb-0.5">Input Preview:</span>
                <pre className="font-mono text-[11px] text-zinc-300 truncate">
                  {JSON.stringify(scen.input || {})}
                </pre>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 font-mono">ID: {scen.id.slice(0, 8)}</span>
              <Button
                size="sm"
                onClick={() => handleRunScenario(scen.id)}
                disabled={runningScenarioId === scen.id}
                className="bg-amber-600 hover:bg-amber-500 text-white text-xs h-7"
              >
                <Play className="w-3 h-3 mr-1" />
                {runningScenarioId === scen.id ? "Running..." : "Test Scenario"}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { SideEffectPreviewPanel } from "@/components/simulation/SideEffectPreviewPanel";
import { AssertionResultsTable } from "@/components/simulation/AssertionResultsTable";
import { simulationService } from "@/services/simulation";
import {
  FlaskConical,
  Play,
  ArrowLeft,
  Settings,
  Layers,
  ShieldCheck,
  Clock,
  Coins,
  RefreshCw,
  AlertCircle,
  FileText,
  Sliders,
  CheckCircle2,
  XCircle,
  Terminal,
} from "lucide-react";

export default function SimulationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const simulationId = params?.simulationId;

  const [simulation, setSimulation] = useState(null);
  const [runs, setRuns] = useState([]);
  const [activeRun, setActiveRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [seedInput, setSeedInput] = useState(42);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const simData = await simulationService.getSimulation(simulationId);
      setSimulation(simData);

      const runList = await simulationService.listSimulationRuns(simulationId, { limit: 10 });
      setRuns(runList || []);
      if (runList && runList.length > 0) {
        // Load details for latest run
        const detail = await simulationService.getRun(runList[0].id);
        setActiveRun(detail);
      }
    } catch (err) {
      console.error("[SimulationDetailPage] Load error:", err);
      setError(err.message || "Failed to load simulation detail.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (simulationId) fetchData();
  }, [simulationId]);

  const handleExecuteRun = async () => {
    try {
      setRunning(true);
      setError(null);
      const newRun = await simulationService.runSimulation(simulationId, {
        seed: Number(seedInput) || 42,
      });
      // Fetch fresh run details
      const detail = await simulationService.getRun(newRun.id);
      setActiveRun(detail);
      setRuns([newRun, ...runs]);
    } catch (err) {
      console.error("[SimulationDetailPage] Run error:", err);
      setError(err.message || "Failed to execute simulation.");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-6xl mx-auto">
        <div className="h-20 bg-zinc-900 animate-pulse rounded-lg" />
        <div className="h-64 bg-zinc-900 animate-pulse rounded-lg" />
      </div>
    );
  }

  if (!simulation) {
    return (
      <div className="p-8 text-center text-zinc-400">
        Simulation not found. <Link href="/app/simulations" className="text-amber-400 underline">Back</Link>
      </div>
    );
  }

  const curVer = simulation.versions?.[0] || {};
  const envConfig = curVer.environment_config || {};

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <Link
        href="/app/simulations"
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Simulations
      </Link>

      <SimulationBanner mode={envConfig.mode || "ISOLATED"} seed={activeRun?.seed || seedInput} />

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5 rounded-lg bg-zinc-900 border border-zinc-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {simulation.target_type}
            </span>
            <h1 className="text-xl font-bold text-zinc-100">{simulation.name}</h1>
            <Badge variant="outline" className="text-xs text-zinc-400 border-zinc-700 font-mono">
              v{curVer.version || 1}
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
            {simulation.description || "Governed sandbox simulation testing environment."}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-zinc-950 px-2.5 py-1 rounded border border-zinc-800 text-xs text-zinc-300">
            <span className="text-zinc-500 font-mono">SEED:</span>
            <input
              type="number"
              value={seedInput}
              onChange={(e) => setSeedInput(e.target.value)}
              className="w-16 bg-transparent text-amber-300 font-mono focus:outline-none"
            />
          </div>

          <Link href={`/app/simulations/${simulation.id}/settings`}>
            <Button variant="outline" size="sm" className="border-zinc-700 text-zinc-300">
              <Settings className="w-4 h-4 mr-1" /> Settings
            </Button>
          </Link>

          <Button
            onClick={handleExecuteRun}
            disabled={running}
            className="bg-amber-600 hover:bg-amber-500 text-white font-medium flex items-center gap-1.5 shadow-md"
          >
            <Play className={`w-4 h-4 ${running ? "animate-spin" : ""}`} />
            {running ? "Running Simulation..." : "Run Simulation"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs / Sub-nav */}
      <div className="flex items-center gap-4 border-b border-zinc-800 pb-2 text-xs font-medium">
        <span className="text-amber-400 border-b-2 border-amber-400 pb-2 font-semibold">Overview & Latest Run</span>
        <Link href={`/app/simulations/${simulation.id}/runs`} className="text-zinc-400 hover:text-zinc-200">
          Run History ({runs.length})
        </Link>
        <Link href={`/app/simulations/${simulation.id}/scenarios`} className="text-zinc-400 hover:text-zinc-200">
          Attached Scenarios
        </Link>
        <Link href={`/app/simulations/${simulation.id}/settings`} className="text-zinc-400 hover:text-zinc-200">
          Policy Overrides & Faults
        </Link>
      </div>

      {/* Active Run Overview */}
      {activeRun ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <StatCard
              title="Execution Status"
              value={activeRun.status.toUpperCase()}
              icon={activeRun.status === "completed" ? CheckCircle2 : XCircle}
              description={`Seed: ${activeRun.seed}`}
            />
            <StatCard
              title="Simulated Cost"
              value={`$${activeRun.cost.toFixed(4)}`}
              icon={Coins}
              description="Zero external API bill"
            />
            <StatCard
              title="Execution Latency"
              value={`${activeRun.latency}s`}
              icon={Clock}
              description="Deterministic timing"
            />
            <StatCard
              title="Side Effects Blocked"
              value={activeRun.side_effects?.length || 0}
              icon={ShieldCheck}
              description="Captured safely in sandbox"
            />
          </div>

          {/* Section 40: Side-Effect Preview Panel */}
          <SideEffectPreviewPanel sideEffects={activeRun.side_effects || []} />

          {/* Section 21: Assertion Results */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                Assertion & Invariant Verification
              </h3>
            </div>
            <AssertionResultsTable assertions={activeRun.assertion_results || []} />
          </Card>

          {/* Output & Execution Trace Preview */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-3">
            <h3 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-purple-400" />
              Simulated Agent Output
            </h3>
            <pre className="font-mono text-xs text-zinc-200 bg-zinc-950 p-4 rounded-lg overflow-x-auto max-h-60 border border-zinc-800">
              {typeof activeRun.output === "object"
                ? JSON.stringify(activeRun.output, null, 2)
                : String(activeRun.output)}
            </pre>
          </Card>
        </div>
      ) : (
        <Card className="p-12 text-center border-zinc-800 bg-zinc-900/40">
          <FlaskConical className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-200">No runs executed yet</h3>
          <p className="text-xs text-zinc-400 mt-1 max-w-sm mx-auto">
            Click 'Run Simulation' above to initiate your first deterministic dry-run.
          </p>
        </Card>
      )}
    </div>
  );
}

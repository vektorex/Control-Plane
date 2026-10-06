"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  FlaskConical,
  Plus,
  Play,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Boxes,
  Zap,
  Sliders,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export default function SimulationsPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [targetTypeFilter, setTargetTypeFilter] = useState("ALL");
  const [error, setError] = useState(null);

  const fetchSimulations = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = targetTypeFilter !== "ALL" ? { target_type: targetTypeFilter.toLowerCase() } : {};
      const data = await simulationService.listSimulations(params);
      setSimulations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[SimulationsPage] Error fetching simulations:", err);
      setError(err.message || "Failed to load simulations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSimulations();
  }, [activeWorkspace, targetTypeFilter]);

  const filteredSimulations = simulations.filter((s) => {
    const q = searchQuery.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.slug.toLowerCase().includes(q) ||
      (s.description && s.description.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <SimulationBanner mode="ISOLATED" seed={42} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-7 h-7 text-amber-400" />
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              AI Simulation & Sandbox
            </h1>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Deterministic dry-runs, synthetic sandboxes, scenario suites, and fault injection without real-world side effects.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/simulations/scenarios">
            <Button variant="outline" className="border-zinc-700 text-zinc-300">
              Scenarios Library
            </Button>
          </Link>
          <Link href="/app/simulations/suites">
            <Button variant="outline" className="border-zinc-700 text-zinc-300">
              Regression Suites
            </Button>
          </Link>
          <Link href="/app/simulations/new">
            <Button className="bg-amber-600 hover:bg-amber-500 text-white font-medium flex items-center gap-1.5 shadow-md">
              <Plus className="w-4 h-4" />
              New Simulation
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Simulations"
          value={simulations.length}
          icon={Boxes}
          description="Governed test configurations"
        />
        <StatCard
          title="Active Sandboxes"
          value={simulations.filter((s) => s.status === "ready" || s.status === "draft").length}
          icon={ShieldCheck}
          description="Isolated test environments"
        />
        <StatCard
          title="Target Types"
          value="5"
          icon={Sliders}
          description="Agents, Teams, Workflows, Tasks, Replay"
        />
        <StatCard
          title="Security Boundary"
          value="100% Guarded"
          icon={AlertTriangle}
          description="Zero external writes executed"
        />
      </div>

      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 rounded-lg bg-zinc-900 border border-zinc-800">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
          <Input
            placeholder="Search simulations by name or slug..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-zinc-950 border-zinc-800 text-sm"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {["ALL", "AGENT", "AGENT_TEAM", "WORKFLOW", "REPLAY"].map((type) => (
            <button
              key={type}
              onClick={() => setTargetTypeFilter(type)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${
                targetTypeFilter === type
                  ? "bg-amber-600/30 text-amber-300 border border-amber-500/40"
                  : "bg-zinc-800/60 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {type}
            </button>
          ))}

          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSimulations}
            className="text-zinc-400 hover:text-zinc-100 p-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-sm flex items-center gap-2">
          <XCircle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simulations Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-lg bg-zinc-900/60 animate-pulse border border-zinc-800" />
          ))}
        </div>
      ) : filteredSimulations.length === 0 ? (
        <Card className="p-12 text-center border-zinc-800 bg-zinc-900/40">
          <FlaskConical className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-zinc-200">No simulations found</h3>
          <p className="text-sm text-zinc-400 mt-1 max-w-sm mx-auto">
            Create an isolated simulation to safely evaluate agents, teams, and policies before production deployment.
          </p>
          <Link href="/app/simulations/new">
            <Button className="mt-4 bg-amber-600 hover:bg-amber-500 text-white font-medium">
              Create First Simulation
            </Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSimulations.map((sim) => (
            <Card
              key={sim.id}
              className="p-5 border-zinc-800 bg-zinc-900/90 hover:border-zinc-700 transition flex flex-col justify-between group shadow-sm"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <Badge variant="outline" className="font-mono text-xs uppercase bg-zinc-800 text-amber-300 border-zinc-700">
                    {sim.target_type}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={
                      sim.status === "ready"
                        ? "text-emerald-400 border-emerald-500/30 bg-emerald-950/20"
                        : "text-zinc-400 border-zinc-700 bg-zinc-800"
                    }
                  >
                    {sim.status.toUpperCase()}
                  </Badge>
                </div>

                <h3 className="text-base font-semibold text-zinc-100 group-hover:text-amber-300 transition">
                  {sim.name}
                </h3>
                <p className="text-xs text-zinc-400 line-clamp-2 mt-1">
                  {sim.description || "No description provided."}
                </p>

                <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-500 font-mono">
                  <span>Target: {sim.target_id.slice(0, 8)}...</span>
                  <span>Slug: {sim.slug}</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between gap-2">
                <Link
                  href={`/app/simulations/${sim.id}`}
                  className="text-xs font-medium text-amber-400 hover:text-amber-300 flex items-center gap-1"
                >
                  Configure & Inspect <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <Link href={`/app/simulations/${sim.id}`}>
                  <Button size="sm" variant="outline" className="h-7 text-xs border-zinc-700 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200">
                    <Play className="w-3 h-3 mr-1 text-amber-400" /> Run
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

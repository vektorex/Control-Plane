"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import {
  Layers,
  Plus,
  Search,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Play,
  ArrowRight,
  RefreshCw,
} from "lucide-react";

export default function ScenariosLibraryPage() {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState(null);

  const fetchScenarios = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = typeFilter !== "ALL" ? { scenario_type: typeFilter.toLowerCase() } : {};
      const data = await simulationService.listScenarios(params);
      setScenarios(data || []);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to load scenarios.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, [typeFilter]);

  const filtered = scenarios.filter((s) => {
    const q = searchQuery.toLowerCase();
    return s.name.toLowerCase().includes(q) || (s.description && s.description.toLowerCase().includes(q));
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <SimulationBanner mode="ISOLATED" seed={42} />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Simulation Scenarios Library
            </h1>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Pre-configured behavioral benchmarks, prompt injection tests, failure profiles, and policy boundary cases.
          </p>
        </div>

        <Link href="/app/simulations/scenarios/new">
          <Button className="bg-amber-600 hover:bg-amber-500 text-white font-medium flex items-center gap-1.5 shadow-md">
            <Plus className="w-4 h-4" /> Visual Scenario Builder
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 rounded-lg bg-zinc-900 border border-zinc-800">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
          <Input
            placeholder="Search scenarios..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-zinc-950 border-zinc-800 text-sm"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
          {["ALL", "NORMAL", "ADVERSARIAL", "SECURITY", "FAILURE", "EDGE_CASE"].map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition ${
                typeFilter === t
                  ? "bg-amber-600/30 text-amber-300 border border-amber-500/40"
                  : "bg-zinc-800/60 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((scen) => (
          <Card key={scen.id} className="p-5 border-zinc-800 bg-zinc-900/90 hover:border-zinc-700 transition flex flex-col justify-between">
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

              <div className="mt-3 p-2.5 rounded bg-zinc-950 border border-zinc-800 text-xs">
                <span className="text-[10px] text-zinc-500 block mb-0.5 font-medium">Input Payload:</span>
                <pre className="font-mono text-[11px] text-zinc-300 truncate">
                  {JSON.stringify(scen.input || {})}
                </pre>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500 font-mono">
              <span>{scen.id.slice(0, 8)}...</span>
              <span className="text-amber-400">Ready</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

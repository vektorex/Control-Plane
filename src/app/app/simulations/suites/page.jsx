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
  Boxes,
  Plus,
  Play,
  Search,
  RefreshCw,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

export default function SimulationSuitesPage() {
  const [suites, setSuites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState(null);

  // New Suite Form
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetType, setTargetType] = useState("agent");
  const [targetId, setTargetId] = useState("");

  const fetchSuites = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await simulationService.listSuites();
      setSuites(data || []);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to load suites.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuites();
  }, []);

  const handleCreateSuite = async (e) => {
    e.preventDefault();
    if (!name.trim() || !targetId.trim()) return;
    try {
      await simulationService.createSuite({
        name: name.trim(),
        description: description.trim() || undefined,
        target_type: targetType,
        target_id: targetId.trim(),
      });
      setShowCreateModal(false);
      setName("");
      setDescription("");
      setTargetId("");
      fetchSuites();
    } catch (err) {
      setError(err.message || "Failed to create suite.");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <SimulationBanner mode="ISOLATED" seed={42} />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Boxes className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Regression Simulation Suites
            </h1>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Bundle scenario batteries into regression suites to catch behavioral regressions before releases.
          </p>
        </div>

        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-amber-600 hover:bg-amber-500 text-white font-medium flex items-center gap-1.5 shadow-md"
        >
          <Plus className="w-4 h-4" /> Create Regression Suite
        </Button>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs">
          {error}
        </div>
      )}

      {/* Suites Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {suites.map((suite) => (
          <Card key={suite.id} className="p-5 border-zinc-800 bg-zinc-900/90 hover:border-zinc-700 transition flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <Badge variant="outline" className="border-zinc-700 bg-zinc-800 text-amber-300 font-mono text-[10px] uppercase">
                  {suite.target_type}
                </Badge>
                <span className="text-[11px] text-zinc-400 font-mono">
                  {suite.status.toUpperCase()}
                </span>
              </div>

              <h3 className="text-base font-semibold text-zinc-100">{suite.name}</h3>
              <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
                {suite.description || "Regression battery for agent verification."}
              </p>

              <div className="mt-3 pt-3 border-t border-zinc-800 text-xs text-zinc-500 font-mono">
                Target: {suite.target_id.slice(0, 8)}...
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between">
              <Link
                href={`/app/simulations/suites/${suite.id}`}
                className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1"
              >
                Inspect Suite <ArrowRight className="w-3.5 h-3.5" />
              </Link>

              <Link href={`/app/simulations/suites/${suite.id}`}>
                <Button size="sm" variant="outline" className="h-7 text-xs border-zinc-700 bg-zinc-800 text-zinc-200">
                  <Play className="w-3 h-3 mr-1 text-amber-400" /> Run Suite
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md p-6 border-zinc-800 bg-zinc-900 space-y-4">
            <h3 className="text-base font-semibold text-zinc-100">Create Regression Suite</h3>
            <form onSubmit={handleCreateSuite} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">Suite Name *</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Agent Pre-Deployment Battery"
                  className="bg-zinc-950 border-zinc-800 text-sm"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">Description</label>
                <Input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Comprehensive regression test suite"
                  className="bg-zinc-950 border-zinc-800 text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">Target Type</label>
                <select
                  value={targetType}
                  onChange={(e) => setTargetType(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 rounded-md p-2 text-sm"
                >
                  <option value="agent">Single Agent</option>
                  <option value="agent_team">Agent Team</option>
                  <option value="workflow">Workflow</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">Target ID *</label>
                <Input
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  placeholder="UUID of Agent or Team"
                  className="bg-zinc-950 border-zinc-800 text-sm font-mono"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)} className="border-zinc-700 text-zinc-300">
                  Cancel
                </Button>
                <Button type="submit" className="bg-amber-600 hover:bg-amber-500 text-white">
                  Create Suite
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}

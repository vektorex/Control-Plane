"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import {
  FlaskConical,
  ArrowLeft,
  ShieldCheck,
  Check,
  AlertTriangle,
  Plus,
  Trash2,
} from "lucide-react";

export default function NewSimulationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form states
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [targetType, setTargetType] = useState("agent");
  const [targetId, setTargetId] = useState("");
  const [targetVersionId, setTargetVersionId] = useState("");
  const [envMode, setEnvMode] = useState("isolated");
  const [maxBudget, setMaxBudget] = useState("1.0");

  // Selected assertions
  const [assertions, setAssertions] = useState([
    { type: "must_complete", value: true, severity: "error" },
    { type: "no_external_side_effect", value: true, severity: "error" },
    { type: "no_secret_exposure", value: true, severity: "error" },
  ]);

  const toggleAssertion = (type) => {
    if (assertions.some((a) => a.type === type)) {
      setAssertions(assertions.filter((a) => a.type !== type));
    } else {
      setAssertions([...assertions, { type, value: true, severity: "error" }]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Simulation name is required.");
      return;
    }
    if (!targetId.trim()) {
      setError("Target ID is required (e.g. Agent ID).");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const payload = {
        name: name.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
        simulation_type: targetType === "agent" ? "single_agent" : targetType,
        target_type: targetType,
        target_id: targetId.trim(),
        target_version_id: targetVersionId.trim() || undefined,
        environment_config: { mode: envMode },
        policy_overrides: {
          max_budget_per_run: parseFloat(maxBudget) || 1.0,
        },
        assertions,
      };

      const res = await simulationService.createSimulation(payload);
      router.push(`/app/simulations/${res.id}`);
    } catch (err) {
      console.error("[NewSimulationPage] Submit error:", err);
      setError(err.message || "Failed to create simulation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link
        href="/app/simulations"
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Simulations
      </Link>

      <SimulationBanner mode={envMode} seed={42} />

      <div>
        <div className="flex items-center gap-2">
          <FlaskConical className="w-6 h-6 text-amber-400" />
          <h1 className="text-xl font-bold tracking-tight text-zinc-100">
            Create Governed Simulation
          </h1>
        </div>
        <p className="text-xs text-zinc-400 mt-1">
          Configure an isolated dry-run sandbox with deterministic assertions and fault boundaries.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Metadata */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">1. Simulation Metadata</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Name *</label>
              <Input
                placeholder="e.g. Security & Injection Sandbox"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-zinc-950 border-zinc-800 text-sm"
                required
              />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Slug (optional)</label>
              <Input
                placeholder="e.g. security-injection-sandbox"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="bg-zinc-950 border-zinc-800 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Description</label>
            <Input
              placeholder="Testing agent behavior against adversarial injection and rate limits"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bg-zinc-950 border-zinc-800 text-sm"
            />
          </div>
        </Card>

        {/* Target Selection */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">2. Execution Target</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: "agent", label: "Single Agent", desc: "Governed AI agent runtime" },
              { id: "agent_team", label: "Agent Team", desc: "Multi-agent coordination" },
              { id: "workflow", label: "Workflow", desc: "Governed workflow graph" },
            ].map((t) => (
              <div
                key={t.id}
                onClick={() => setTargetType(t.id)}
                className={`p-3 rounded-lg border cursor-pointer transition ${
                  targetType === t.id
                    ? "border-amber-500 bg-amber-950/20 text-amber-200"
                    : "border-zinc-800 bg-zinc-950/60 text-zinc-400 hover:border-zinc-700"
                }`}
              >
                <div className="font-semibold text-xs text-zinc-100">{t.label}</div>
                <div className="text-[11px] text-zinc-500 mt-0.5">{t.desc}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Target ID *</label>
              <Input
                placeholder="UUID or Identifier of Target"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                className="bg-zinc-950 border-zinc-800 text-sm font-mono"
                required
              />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Target Version ID (optional)</label>
              <Input
                placeholder="Leave blank for latest active version"
                value={targetVersionId}
                onChange={(e) => setTargetVersionId(e.target.value)}
                className="bg-zinc-950 border-zinc-800 text-sm font-mono"
              />
            </div>
          </div>
        </Card>

        {/* Environment & Policy Overrides */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">3. Environment & Policy Overrides</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: "isolated", label: "Isolated", desc: "Zero state persistence" },
              { id: "snapshot", label: "Snapshot", desc: "Sanitized read-only snapshot" },
              { id: "synthetic", label: "Synthetic", desc: "Mocked tools & documents" },
            ].map((env) => (
              <div
                key={env.id}
                onClick={() => setEnvMode(env.id)}
                className={`p-3 rounded-lg border cursor-pointer transition ${
                  envMode === env.id
                    ? "border-amber-500 bg-amber-950/20 text-amber-200"
                    : "border-zinc-800 bg-zinc-950/60 text-zinc-400 hover:border-zinc-700"
                }`}
              >
                <div className="font-semibold text-xs text-zinc-100">{env.label}</div>
                <div className="text-[11px] text-zinc-500 mt-0.5">{env.desc}</div>
              </div>
            ))}
          </div>

          <div className="w-full sm:w-1/2 pt-2">
            <label className="text-xs font-medium text-zinc-400 block mb-1">Max Simulation Budget ($)</label>
            <Input
              type="number"
              step="0.1"
              value={maxBudget}
              onChange={(e) => setMaxBudget(e.target.value)}
              className="bg-zinc-950 border-zinc-800 text-sm font-mono"
            />
          </div>
        </Card>

        {/* Invariant Assertions */}
        <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200">4. Invariant Assertions</h2>
          <p className="text-xs text-zinc-400">
            Select deterministic policy and security invariants to verify during every simulation run.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {[
              { id: "must_complete", label: "Must Complete Run" },
              { id: "no_external_side_effect", label: "No External Side Effects (Sandbox Intercept)" },
              { id: "no_secret_exposure", label: "No Secret Exposure (API keys / tokens)" },
              { id: "no_privilege_escalation", label: "No Privilege Escalation" },
              { id: "no_cross_tenant_access", label: "No Cross-Tenant Boundary Crossing" },
              { id: "policy_must_allow", label: "Governance Policy Must Allow" },
            ].map((item) => {
              const active = assertions.some((a) => a.type === item.id);
              return (
                <div
                  key={item.id}
                  onClick={() => toggleAssertion(item.id)}
                  className={`p-2.5 rounded-md border text-xs cursor-pointer flex items-center justify-between transition ${
                    active
                      ? "border-amber-500/50 bg-amber-950/30 text-amber-200 font-medium"
                      : "border-zinc-800 bg-zinc-950/40 text-zinc-400 hover:border-zinc-700"
                  }`}
                >
                  <span>{item.label}</span>
                  {active && <Check className="w-4 h-4 text-amber-400" />}
                </div>
              );
            })}
          </div>
        </Card>

        <div className="flex items-center justify-end gap-3 pt-2">
          <Link href="/app/simulations">
            <Button variant="outline" className="border-zinc-700 text-zinc-300">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={loading}
            className="bg-amber-600 hover:bg-amber-500 text-white font-medium px-6 shadow-md"
          >
            {loading ? "Creating..." : "Save Simulation"}
          </Button>
        </div>
      </form>
    </div>
  );
}

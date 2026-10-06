"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { SimulationBanner } from "@/components/simulation/SimulationBanner";
import { simulationService } from "@/services/simulation";
import {
  FlaskConical,
  ArrowLeft,
  Settings,
  ShieldCheck,
  Save,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";

export default function SimulationSettingsPage() {
  const params = useParams();
  const router = useRouter();
  const simulationId = params?.simulationId;

  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form states
  const [simName, setSimName] = useState("");
  const [simDescription, setSimDescription] = useState("");
  const [maxBudget, setMaxBudget] = useState("1.0");
  const [requireApproval, setRequireApproval] = useState(false);
  const [disableConnectors, setDisableConnectors] = useState(false);
  const [envMode, setEnvMode] = useState("isolated");

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await simulationService.getSimulation(simulationId);
        setSimulation(data);
        setSimName(data.name || "");
        setSimDescription(data.description || "");

        const curVer = data.versions?.[0] || {};
        const pol = curVer.policy_overrides || {};
        setMaxBudget(pol.max_budget_per_run || "1.0");
        setRequireApproval(Boolean(pol.require_approval_all));
        setDisableConnectors(Boolean(pol.disabled_connectors?.length));
        setEnvMode(curVer.environment_config?.mode || "isolated");
      } catch (err) {
        console.error(err);
        setError("Failed to load settings.");
      } finally {
        setLoading(false);
      }
    }
    if (simulationId) load();
  }, [simulationId]);

  const handlePublishNewVersion = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      // Create new version
      const verPayload = {
        configuration: {},
        environment_config: { mode: envMode },
        policy_overrides: {
          max_budget_per_run: parseFloat(maxBudget) || 1.0,
          require_approval_all: requireApproval,
          disabled_connectors: disableConnectors ? ["github", "slack"] : [],
        },
        publish_immediately: true,
      };

      await simulationService.createVersion(simulationId, verPayload);
      await simulationService.updateSimulation(simulationId, {
        name: simName,
        description: simDescription,
      });

      setSuccess("Published new immutable simulation version successfully.");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to update configuration.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-zinc-400">Loading settings...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <Link
        href={`/app/simulations/${simulationId}`}
        className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Simulation
      </Link>

      <SimulationBanner mode={envMode} seed={42} />

      <div>
        <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
          <Settings className="w-5 h-5 text-amber-400" />
          Simulation Configuration & Versions
        </h1>
        <p className="text-xs text-zinc-400 mt-1">
          Published simulation versions are immutable. Updating parameters creates and publishes a new immutable version.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-3.5 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-200">General Simulation Info</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Name</label>
            <Input
              value={simName}
              onChange={(e) => setSimName(e.target.value)}
              className="bg-zinc-950 border-zinc-800 text-sm"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Description</label>
            <Input
              value={simDescription}
              onChange={(e) => setSimDescription(e.target.value)}
              className="bg-zinc-950 border-zinc-800 text-sm"
            />
          </div>
        </div>
      </Card>

      <Card className="p-5 border-zinc-800 bg-zinc-900/80 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-200">Policy Overrides (Simulation Only)</h2>
        <p className="text-xs text-zinc-400">
          Simulate governance rules without modifying production policies.
        </p>

        <div className="space-y-3 pt-2">
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Max Budget Cap ($)</label>
            <Input
              type="number"
              step="0.1"
              value={maxBudget}
              onChange={(e) => setMaxBudget(e.target.value)}
              className="bg-zinc-950 border-zinc-800 text-sm font-mono max-w-xs"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <input
              type="checkbox"
              id="requireApproval"
              checked={requireApproval}
              onChange={(e) => setRequireApproval(e.target.checked)}
              className="rounded bg-zinc-950 border-zinc-800 text-amber-500 focus:ring-0"
            />
            <label htmlFor="requireApproval" className="text-xs text-zinc-300">
              Require Simulated HITL Approval for all critical actions
            </label>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="disableConnectors"
              checked={disableConnectors}
              onChange={(e) => setDisableConnectors(e.target.checked)}
              className="rounded bg-zinc-950 border-zinc-800 text-amber-500 focus:ring-0"
            />
            <label htmlFor="disableConnectors" className="text-xs text-zinc-300">
              Simulate disabled external connectors (GitHub, Slack)
            </label>
          </div>
        </div>
      </Card>

      <div className="flex justify-end gap-3">
        <Button
          onClick={handlePublishNewVersion}
          disabled={saving}
          className="bg-amber-600 hover:bg-amber-500 text-white font-medium px-6 shadow-md"
        >
          {saving ? "Publishing..." : "Publish New Immutable Version"}
        </Button>
      </div>
    </div>
  );
}

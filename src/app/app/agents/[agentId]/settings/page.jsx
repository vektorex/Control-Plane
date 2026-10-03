"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  ArrowLeft,
  Bot,
  Sliders,
  ShieldCheck,
  CheckCircle2,
  Pause,
  AlertTriangle,
  Lock,
  Sparkles,
} from "lucide-react";

export default function AgentSettingsPage({ params }) {
  const unwrappedParams = use(params);
  const { agentId } = unwrappedParams;
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [agent, setAgent] = useState(null);
  const [policyPreview, setPolicyPreview] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [purpose, setPurpose] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ag, preview] = await Promise.all([
        agentService.getAgent(agentId),
        agentService.previewAgentPolicy(agentId).catch(() => null),
      ]);
      setAgent(ag);
      setName(ag.name);
      setDescription(ag.description || "");
      setPurpose(ag.purpose || "");
      setPolicyPreview(preview);
    } catch (err) {
      console.error("Failed to load agent settings:", err);
      setError(err.message || "Failed to load agent configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (agentId) {
      loadData();
    }
  }, [agentId, activeWorkspace]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);
      await agentService.updateAgent(agentId, {
        name: name.trim(),
        description: description.trim() || undefined,
        purpose: purpose.trim(),
      });
      setSuccessMsg("Agent metadata updated successfully.");
      await loadData();
    } catch (err) {
      setError(err.message || "Failed to update agent");
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async () => {
    try {
      setActionLoading(true);
      await agentService.activateAgent(agentId);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to activate agent");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      setActionLoading(true);
      await agentService.pauseAgent(agentId);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to pause agent");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-16 rounded-xl bg-zinc-900 border border-zinc-800" />
        <div className="h-64 rounded-xl bg-zinc-900 border border-zinc-800" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-zinc-800/80 pb-5">
        <Link
          href={`/app/agents/${agentId}`}
          className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-zinc-100">{agent?.name} — Settings & Boundaries</h1>
            <Badge
              variant={
                agent?.status === "active"
                  ? "success"
                  : agent?.status === "paused"
                  ? "warning"
                  : "default"
              }
              className="text-[10px] capitalize"
            >
              {agent?.status}
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Configure agent identity, inspect effective policy previews, and manage execution lifecycle.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl border border-red-500/20 bg-red-500/10 text-red-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Metadata Form */}
      <form onSubmit={handleUpdate} className="space-y-6">
        <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-purple-400" />
            <span>Agent Metadata</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Slug (Immutable)</label>
              <Input
                value={agent?.slug || ""}
                disabled
                className="text-xs bg-zinc-900/50 border-zinc-800 text-zinc-500 font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-zinc-300">Purpose Statement</label>
            <textarea
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              rows={2}
              className="w-full text-xs bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-zinc-200 focus:outline-none focus:border-purple-500"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-zinc-300">Description</label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="text-xs bg-zinc-900 border-zinc-800 text-zinc-200"
            />
          </div>

          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              size="sm"
              disabled={saving}
              className="bg-purple-600 hover:bg-purple-500 text-white text-xs"
            >
              {saving ? "Saving Changes..." : "Save Metadata"}
            </Button>
          </div>
        </Card>
      </form>

      {/* Effective Policy Preview */}
      {policyPreview && (
        <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              <span>Effective Policy Boundary Preview</span>
            </h2>
            <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-800">
              Resolved Configuration
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1.5 text-zinc-300">
              <span className="font-semibold text-zinc-400 uppercase tracking-wider block text-[10px] font-sans">
                Allowed Capabilities
              </span>
              <div className="flex flex-wrap gap-1">
                {(policyPreview.allowed_capabilities || []).map((c) => (
                  <span
                    key={c}
                    className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 text-[10px] border border-purple-500/20"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1.5 text-zinc-300">
              <span className="font-semibold text-zinc-400 uppercase tracking-wider block text-[10px] font-sans">
                Execution Limits
              </span>
              <div>Max Steps: {policyPreview.execution_limits?.max_steps ?? 20}</div>
              <div>Max Runtime: {policyPreview.execution_limits?.max_runtime_seconds ?? 300}s</div>
              <div>Max Budget: ${policyPreview.budget_policy?.max_cost_per_run ?? 1.0}</div>
            </div>
          </div>
        </Card>
      )}

      {/* Lifecycle Controls */}
      <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <Lock className="w-4 h-4 text-purple-400" />
          <span>Lifecycle Management</span>
        </h2>
        <p className="text-xs text-zinc-400">
          Suspending or pausing an agent prevents any user, trigger, or multi-agent team from executing new runs.
        </p>

        <div className="flex items-center gap-3 pt-2">
          {agent?.status === "active" ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handlePause}
              disabled={actionLoading}
              className="border-zinc-800 text-amber-400 hover:bg-amber-500/10 gap-1.5 text-xs"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause Agent Execution</span>
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleActivate}
              disabled={actionLoading}
              className="border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10 gap-1.5 text-xs"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Activate Agent</span>
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

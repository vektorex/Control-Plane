"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { agentService } from "@/services/agents";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  ArrowLeft,
  Boxes,
  Sliders,
  ShieldCheck,
  CheckCircle2,
  Pause,
  AlertTriangle,
  Lock,
} from "lucide-react";

export default function AgentTeamSettingsPage({ params }) {
  const unwrappedParams = use(params);
  const { teamId } = unwrappedParams;
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [team, setTeam] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const t = await agentService.getTeam(teamId);
      setTeam(t);
      setName(t.name);
      setDescription(t.description || "");
    } catch (err) {
      console.error("Failed to load team settings:", err);
      setError(err.message || "Failed to load team configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (teamId) {
      loadData();
    }
  }, [teamId, activeWorkspace]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);
      await agentService.updateTeam(teamId, {
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setSuccessMsg("Team metadata updated successfully.");
      await loadData();
    } catch (err) {
      setError(err.message || "Failed to update team");
    } finally {
      setSaving(false);
    }
  };

  const handleActivate = async () => {
    try {
      setActionLoading(true);
      await agentService.activateTeam(teamId);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to activate team");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      setActionLoading(true);
      await agentService.pauseTeam(teamId);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to pause team");
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
          href={`/app/agent-teams/${teamId}`}
          className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-zinc-100">{team?.name} — Team Settings</h1>
            <Badge
              variant={
                team?.status === "active"
                  ? "success"
                  : team?.status === "paused"
                  ? "warning"
                  : "default"
              }
              className="text-[10px] capitalize"
            >
              {team?.status}
            </Badge>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Configure multi-agent team metadata, coordination boundaries, and manage team lifecycle.
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

      {/* Form */}
      <form onSubmit={handleUpdate} className="space-y-6">
        <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-purple-400" />
            <span>Team Metadata</span>
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
                value={team?.slug || ""}
                disabled
                className="text-xs bg-zinc-900/50 border-zinc-800 text-zinc-500 font-mono"
              />
            </div>
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

      {/* Lifecycle Controls */}
      <Card className="p-6 border-zinc-800 bg-zinc-950/70 space-y-4">
        <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
          <Lock className="w-4 h-4 text-purple-400" />
          <span>Team Lifecycle Management</span>
        </h2>
        <p className="text-xs text-zinc-400">
          Pausing a team suspends coordinated run execution while preserving individual agent statuses and historical run audits.
        </p>

        <div className="flex items-center gap-3 pt-2">
          {team?.status === "active" ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handlePause}
              disabled={actionLoading}
              className="border-zinc-800 text-amber-400 hover:bg-amber-500/10 gap-1.5 text-xs"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause Team Execution</span>
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
              <span>Activate Team</span>
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { outcomeService } from "@/services/outcomes";
import {
  Layers,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  Box,
  Cpu,
  FileText,
  GitCommit,
  CheckCircle2,
} from "lucide-react";

export default function OutcomeWorkPage() {
  const params = useParams();
  const outcomeId = params.outcomeId;

  const [workLinks, setWorkLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    resource_type: "task",
    resource_id: "",
    relationship: "contributes_to",
  });

  const fetchWorkLinks = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.listWorkLinks(outcomeId);
      setWorkLinks(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[OutcomeWorkPage] Error:", err);
      setError(err.message || "Failed to load linked work");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (outcomeId) fetchWorkLinks();
  }, [outcomeId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.resource_id.trim()) return;

    try {
      setSubmitting(true);
      const payload = {
        resource_type: form.resource_type,
        resource_id: form.resource_id.trim(),
        relationship: form.relationship,
      };

      await outcomeService.addWorkLink(outcomeId, payload);
      setIsModalOpen(false);
      setForm({ resource_type: "task", resource_id: "", relationship: "contributes_to" });
      fetchWorkLinks();
    } catch (err) {
      console.error("[OutcomeWorkPage] Error adding work link:", err);
      alert(err.message || "Failed to link work resource");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/app/outcomes/${outcomeId}`}>
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Back to Outcome
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm font-semibold text-zinc-200">Connected Work Resources</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Link Work Resource
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <Layers className="h-6 w-6 text-indigo-400" />
          Linked Work Executions
        </h1>
        <p className="text-sm text-zinc-400">
          Connect Tasks, Agent Runs, Workflows, Artifacts, and Evaluations to the outcome they produced or supported.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-zinc-500" />
        </div>
      ) : workLinks.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <Layers className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No work resources linked</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Link AI tasks, agent teams, and workflow executions to track what produced this deliverable.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Link First Resource
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {workLinks.map((wl) => (
            <Card key={wl.id} className="p-4 bg-zinc-900/60 border-zinc-800 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-zinc-950 border border-zinc-800">
                  <Box className="h-4 w-4 text-indigo-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase text-zinc-200">
                      {wl.resource_type}
                    </span>
                    <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-[10px]">
                      {wl.relationship}
                    </Badge>
                  </div>
                  <div className="font-mono text-xs text-zinc-400 mt-0.5">
                    ID: {wl.resource_id}
                  </div>
                </div>
              </div>

              <div className="text-right text-xs text-zinc-500 font-mono shrink-0">
                Created: {new Date(wl.created_at).toLocaleDateString()}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Link Resource Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Link Work Execution">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Resource Type *</label>
            <select
              value={form.resource_type}
              onChange={(e) => setForm((p) => ({ ...p, resource_type: e.target.value }))}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
            >
              <option value="task">Task</option>
              <option value="run">Run</option>
              <option value="workflow">Workflow</option>
              <option value="workflow_run">Workflow Run</option>
              <option value="agent_run">Agent Run</option>
              <option value="agent_team_run">Agent Team Run</option>
              <option value="artifact">Artifact Deliverable</option>
              <option value="evaluation_run">Evaluation Run</option>
              <option value="simulation_run">Simulation Run</option>
              <option value="decision">Decision</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Resource ID *</label>
            <Input
              value={form.resource_id}
              onChange={(e) => setForm((p) => ({ ...p, resource_id: e.target.value }))}
              placeholder="UUID of Task, Run, or Workflow"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Relationship</label>
            <select
              value={form.relationship}
              onChange={(e) => setForm((p) => ({ ...p, relationship: e.target.value }))}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
            >
              <option value="contributes_to">contributes_to</option>
              <option value="produced">produced</option>
              <option value="supports">supports</option>
              <option value="validated_by">validated_by</option>
              <option value="blocked_by">blocked_by</option>
              <option value="derived_from">derived_from</option>
              <option value="measures">measures</option>
              <option value="implements">implements</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={submitting}
              className="bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              {submitting ? "Linking..." : "Link Resource"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

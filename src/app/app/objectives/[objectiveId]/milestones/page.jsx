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
  ListTodo,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Clock,
  XCircle,
} from "lucide-react";

export default function ObjectiveMilestonesPage() {
  const params = useParams();
  const objectiveId = params.objectiveId;

  const [milestones, setMilestones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: "",
    description: "",
    due_at: "",
    status: "planned",
  });

  const fetchMilestones = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.listMilestones(objectiveId);
      setMilestones(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[ObjectiveMilestonesPage] Error:", err);
      setError(err.message || "Failed to load milestones");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (objectiveId) fetchMilestones();
  }, [objectiveId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      setSubmitting(true);
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
        status: form.status,
      };

      await outcomeService.createMilestone(objectiveId, payload);
      setIsModalOpen(false);
      setForm({ name: "", description: "", due_at: "", status: "planned" });
      fetchMilestones();
    } catch (err) {
      console.error("[ObjectiveMilestonesPage] Create milestone error:", err);
      alert(err.message || "Failed to create milestone");
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
      case "blocked":
        return <AlertTriangle className="h-4 w-4 text-rose-400" />;
      case "missed":
        return <XCircle className="h-4 w-4 text-amber-400" />;
      default:
        return <Clock className="h-4 w-4 text-zinc-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/app/objectives/${objectiveId}`}>
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Back to Objective
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm font-semibold text-zinc-200">Milestones</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Add Milestone
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <ListTodo className="h-6 w-6 text-blue-400" />
          Strategic Milestones & Checkpoints
        </h1>
        <p className="text-sm text-zinc-400">
          Track stage-gate completion and blocker status for tasks, workflows, and approvals.
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
      ) : milestones.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <ListTodo className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No milestones configured</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Establish critical checkpoints to verify progress before downstream steps execute.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Add First Milestone
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {milestones.map((m) => (
            <Card key={m.id} className="p-4 bg-zinc-900/60 border-zinc-800 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="mt-0.5">{getStatusIcon(m.status)}</div>
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-zinc-100">{m.name}</h3>
                  <p className="text-xs text-zinc-400">{m.description || "No description"}</p>
                  {m.due_at && (
                    <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-mono">
                      <Calendar className="h-3 w-3" />
                      Due: {new Date(m.due_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Badge className={`text-xs uppercase font-mono ${
                  m.status === "completed"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : m.status === "blocked"
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    : m.status === "missed"
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    : "bg-zinc-800 text-zinc-400 border-zinc-700"
                }`}>
                  {m.status}
                </Badge>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Milestone Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add Milestone">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Milestone Name *</label>
            <Input
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g. Complete architecture review & security approval"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Description</label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={2}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Due Date</label>
              <Input
                type="date"
                name="due_at"
                value={form.due_at}
                onChange={handleChange}
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Initial Status</label>
              <select
                name="status"
                value={form.status}
                onChange={handleChange}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
              >
                <option value="planned">Planned</option>
                <option value="in_progress">In Progress</option>
                <option value="blocked">Blocked</option>
                <option value="completed">Completed</option>
              </select>
            </div>
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
              {submitting ? "Saving..." : "Create Milestone"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

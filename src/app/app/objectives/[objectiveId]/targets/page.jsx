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
  Target,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  Calendar,
  Layers,
  CheckCircle2,
} from "lucide-react";

export default function ObjectiveTargetsPage() {
  const params = useParams();
  const objectiveId = params.objectiveId;

  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: "",
    description: "",
    metric_type: "count",
    target_value: "",
    target_unit: "",
    baseline_value: "",
    measurement_source: "system",
    target_date: "",
  });

  const fetchTargets = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.listTargets(objectiveId);
      setTargets(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[ObjectiveTargetsPage] Fetch error:", err);
      setError(err.message || "Failed to load targets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (objectiveId) fetchTargets();
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
        metric_type: form.metric_type,
        target_value: form.target_value ? parseFloat(form.target_value) : null,
        target_unit: form.target_unit.trim() || null,
        baseline_value: form.baseline_value ? parseFloat(form.baseline_value) : null,
        measurement_source: form.measurement_source,
        target_date: form.target_date ? new Date(form.target_date).toISOString() : null,
      };

      await outcomeService.createTarget(objectiveId, payload);
      setIsModalOpen(false);
      setForm({
        name: "",
        description: "",
        metric_type: "count",
        target_value: "",
        target_unit: "",
        baseline_value: "",
        measurement_source: "system",
        target_date: "",
      });
      fetchTargets();
    } catch (err) {
      console.error("[ObjectiveTargetsPage] Create target error:", err);
      alert(err.message || "Failed to create target");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/app/objectives/${objectiveId}`}>
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Back to Objective
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm font-semibold text-zinc-200">Key Results & Targets</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Add Target
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <Target className="h-6 w-6 text-indigo-400" />
          Factual Targets & Key Results
        </h1>
        <p className="text-sm text-zinc-400">
          Target values must be grounded in measurable sources. Baselines cannot be fabricated.
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
      ) : targets.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <Target className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No targets configured</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Define factual key results with baseline metrics and measurement sources.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Create First Target
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {targets.map((target) => (
            <Card key={target.id} className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-100">{target.name}</h3>
                  <p className="text-xs text-zinc-400 mt-0.5">{target.description || "No description"}</p>
                </div>
                <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 text-[10px] uppercase">
                  {target.status}
                </Badge>
              </div>

              <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80 text-center font-mono">
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Baseline</div>
                  <div className="text-sm font-bold text-zinc-400">{target.baseline_value ?? "—"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Current</div>
                  <div className="text-sm font-bold text-zinc-100">{target.current_value ?? "—"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Target</div>
                  <div className="text-sm font-bold text-indigo-400">
                    {target.target_value ?? "—"} {target.target_unit || ""}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-2 border-t border-zinc-800/60">
                <span>Source: <strong className="text-zinc-400">{target.measurement_source}</strong></span>
                <span>Type: <strong className="text-zinc-400">{target.metric_type}</strong></span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Target Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add Key Result Target">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Target Name *</label>
            <Input
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g. Reduce mean time to remediate (MTTR)"
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
              <label className="block text-xs font-medium text-zinc-300 mb-1">Metric Type</label>
              <select
                name="metric_type"
                value={form.metric_type}
                onChange={handleChange}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
              >
                <option value="count">Count</option>
                <option value="percentage">Percentage (%)</option>
                <option value="duration">Duration (minutes/hours)</option>
                <option value="currency">Currency ($)</option>
                <option value="rate">Rate</option>
                <option value="ratio">Ratio</option>
                <option value="boolean">Boolean</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Measurement Source</label>
              <select
                name="measurement_source"
                value={form.measurement_source}
                onChange={handleChange}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
              >
                <option value="system">System</option>
                <option value="workflow">Workflow</option>
                <option value="evaluation">Evaluation Lab</option>
                <option value="event">Event Bus</option>
                <option value="connector">Connector</option>
                <option value="artifact">Artifact</option>
                <option value="manual">Manual</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Baseline Value</label>
              <Input
                type="number"
                step="any"
                name="baseline_value"
                value={form.baseline_value}
                onChange={handleChange}
                placeholder="e.g. 90"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Target Value</label>
              <Input
                type="number"
                step="any"
                name="target_value"
                value={form.target_value}
                onChange={handleChange}
                placeholder="e.g. 45"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Unit</label>
              <Input
                name="target_unit"
                value={form.target_unit}
                onChange={handleChange}
                placeholder="e.g. minutes, %"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Target Date</label>
            <Input
              type="date"
              name="target_date"
              value={form.target_date}
              onChange={handleChange}
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
            />
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
              {submitting ? "Saving..." : "Create Target"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

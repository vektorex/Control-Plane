"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { outcomeService } from "@/services/outcomes";
import {
  Target,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  ShieldCheck,
  AlertCircle,
  FileText,
} from "lucide-react";

export default function NewObjectivePage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    name: "",
    description: "",
    objective_type: "business",
    priority: "medium",
    start_at: "",
    target_at: "",
    required_evidence: true,
    required_approval: false,
    required_evaluation: false,
    required_human_confirmation: false,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("Objective name is required");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        objective_type: form.objective_type,
        priority: form.priority,
        start_at: form.start_at ? new Date(form.start_at).toISOString() : null,
        target_at: form.target_at ? new Date(form.target_at).toISOString() : null,
        properties: {
          verification_requirements: {
            required_evidence: form.required_evidence,
            required_approval: form.required_approval,
            required_evaluation: form.required_evaluation,
            required_human_confirmation: form.required_human_confirmation,
          },
        },
      };

      const res = await outcomeService.createObjective(payload);
      if (res && res.id) {
        router.push(`/app/objectives/${res.id}`);
      } else {
        router.push("/app/objectives");
      }
    } catch (err) {
      console.error("[NewObjectivePage] Create failed:", err);
      setError(err.message || "Failed to create objective");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/app/objectives">
          <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
            <ArrowLeft className="h-4 w-4" />
            Back to Objectives
          </Button>
        </Link>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <Target className="h-6 w-6 text-indigo-400" />
          Create New Strategic Objective
        </h1>
        <p className="text-sm text-zinc-400">
          Define the high-level business, product, or engineering goal that AI work will be attributed to.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="p-6 bg-zinc-900/60 border-zinc-800 space-y-6">
          <h2 className="text-base font-semibold text-zinc-200 flex items-center gap-2 border-b border-zinc-800/80 pb-3">
            <FileText className="h-4 w-4 text-indigo-400" />
            Objective Details
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Objective Name <span className="text-rose-400">*</span>
              </label>
              <Input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="e.g. Accelerate Tier-1 Incident Resolution & Prevent Regressions"
                className="bg-zinc-950 border-zinc-800 text-zinc-100"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Description & Desired Impact
              </label>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                rows={4}
                placeholder="Explain the tangible business outcome, why it matters, and what evidence will prove success..."
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Objective Type
                </label>
                <select
                  name="objective_type"
                  value={form.objective_type}
                  onChange={handleChange}
                  className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="business">Business</option>
                  <option value="product">Product</option>
                  <option value="engineering">Engineering</option>
                  <option value="research">Research</option>
                  <option value="operations">Operations</option>
                  <option value="security">Security</option>
                  <option value="compliance">Compliance</option>
                  <option value="project">Project</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Priority
                </label>
                <select
                  name="priority"
                  value={form.priority}
                  onChange={handleChange}
                  className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="critical">Critical (P0)</option>
                  <option value="high">High (P1)</option>
                  <option value="medium">Medium (P2)</option>
                  <option value="low">Low (P3)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Start Date
                </label>
                <Input
                  type="date"
                  name="start_at"
                  value={form.start_at}
                  onChange={handleChange}
                  className="bg-zinc-950 border-zinc-800 text-zinc-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Target Completion Date
                </label>
                <Input
                  type="date"
                  name="target_at"
                  value={form.target_at}
                  onChange={handleChange}
                  className="bg-zinc-950 border-zinc-800 text-zinc-100"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Verification Requirements */}
        <Card className="p-6 bg-zinc-900/60 border-zinc-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-800/80 pb-3">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <div>
              <h2 className="text-base font-semibold text-zinc-200">
                Outcome Verification Requirements
              </h2>
              <p className="text-xs text-zinc-400">
                Outcomes linked to this objective cannot transition to VERIFIED without meeting these deterministic conditions.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <label className="flex items-start gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-950/60 cursor-pointer hover:border-zinc-700">
              <input
                type="checkbox"
                name="required_evidence"
                checked={form.required_evidence}
                onChange={handleChange}
                className="mt-1 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-500 bg-zinc-900"
              />
              <div>
                <div className="text-sm font-medium text-zinc-200">Evidence Required</div>
                <div className="text-xs text-zinc-400">At least one verified evidence snapshot must support each deliverable.</div>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-950/60 cursor-pointer hover:border-zinc-700">
              <input
                type="checkbox"
                name="required_human_confirmation"
                checked={form.required_human_confirmation}
                onChange={handleChange}
                className="mt-1 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-500 bg-zinc-900"
              />
              <div>
                <div className="text-sm font-medium text-zinc-200">Human Sign-off Required</div>
                <div className="text-xs text-zinc-400">AI cannot mark outcomes verified without explicit human confirmation.</div>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-950/60 cursor-pointer hover:border-zinc-700">
              <input
                type="checkbox"
                name="required_approval"
                checked={form.required_approval}
                onChange={handleChange}
                className="mt-1 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-500 bg-zinc-900"
              />
              <div>
                <div className="text-sm font-medium text-zinc-200">Policy / HITL Approval</div>
                <div className="text-xs text-zinc-400">Requires an approved governance decision record.</div>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-950/60 cursor-pointer hover:border-zinc-700">
              <input
                type="checkbox"
                name="required_evaluation"
                checked={form.required_evaluation}
                onChange={handleChange}
                className="mt-1 rounded border-zinc-700 text-indigo-600 focus:ring-indigo-500 bg-zinc-900"
              />
              <div>
                <div className="text-sm font-medium text-zinc-200">Evaluation Lab Passed</div>
                <div className="text-xs text-zinc-400">Requires an associated evaluation run with passing assertions.</div>
              </div>
            </label>
          </div>
        </Card>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Link href="/app/objectives">
            <Button type="button" variant="ghost" disabled={submitting}>
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={submitting}
            className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2"
          >
            {submitting ? "Creating Objective..." : "Create Objective"}
          </Button>
        </div>
      </form>
    </div>
  );
}

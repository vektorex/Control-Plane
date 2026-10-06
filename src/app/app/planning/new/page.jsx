"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { planningService } from "@/services/planning";
import {
  CalendarRange,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Sliders,
  Sparkles,
} from "lucide-react";

export default function NewPlanPage() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    planning_mode: "assisted",
    objective_id: "",
    planning_horizon_start: new Date().toISOString().slice(0, 16),
    planning_horizon_end: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("Plan name is required.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const payload = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        planning_mode: formData.planning_mode,
        objective_id: formData.objective_id.trim() || null,
        planning_horizon_start: formData.planning_horizon_start ? new Date(formData.planning_horizon_start).toISOString() : null,
        planning_horizon_end: formData.planning_horizon_end ? new Date(formData.planning_horizon_end).toISOString() : null,
      };

      const created = await planningService.createWorkPlan(payload);
      router.push(`/app/planning/${created.id}`);
    } catch (err) {
      console.error("[NewPlanPage] Creation error:", err);
      setError(err.message || "Failed to create work plan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-4xl mx-auto">
      {/* Back button & Header */}
      <div>
        <Link href="/app/planning">
          <Button variant="ghost" size="sm" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Plans
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
            <CalendarRange className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Create Work Plan
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Set planning horizon, optimization mode, and associate with target outcomes.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <Card className="p-6 md:p-8 border-border/60">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Plan Name <span className="text-destructive">*</span>
            </label>
            <Input
              placeholder="e.g. Q4 Platform Hardening & Release Sequence"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Description & Planning Goal
            </label>
            <textarea
              rows={4}
              placeholder="Detail the scope, key deliverables, and constraints..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">
                Planning Mode
              </label>
              <select
                value={formData.planning_mode}
                onChange={(e) => setFormData({ ...formData, planning_mode: e.target.value })}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="assisted">Assisted (Rule-based with AI suggestions)</option>
                <option value="manual">Manual (Explicit sequencing only)</option>
                <option value="optimized">Optimized (Heuristic schedule candidate generation)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">
                Associated Objective ID (Optional)
              </label>
              <Input
                placeholder="UUID of target objective"
                value={formData.objective_id}
                onChange={(e) => setFormData({ ...formData, objective_id: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">
                Planning Horizon Start
              </label>
              <Input
                type="datetime-local"
                value={formData.planning_horizon_start}
                onChange={(e) => setFormData({ ...formData, planning_horizon_start: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">
                Planning Horizon End
              </label>
              <Input
                type="datetime-local"
                value={formData.planning_horizon_end}
                onChange={(e) => setFormData({ ...formData, planning_horizon_end: e.target.value })}
              />
            </div>
          </div>

          <div className="pt-4 border-t border-border/40 flex items-center justify-end gap-3">
            <Link href="/app/planning">
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={loading} className="gap-2">
              <CheckCircle2 className="w-4 h-4" />
              {loading ? "Creating..." : "Initialize Plan"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

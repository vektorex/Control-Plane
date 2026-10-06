"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { planningService } from "@/services/planning";
import {
  CalendarRange,
  ArrowLeft,
  Play,
  Pause,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Clock,
  Activity,
  Plus,
  Network,
  Users2,
  Sliders,
  Sparkles,
  GitCommit,
  Check,
  RefreshCw,
} from "lucide-react";

export default function PlanDetailPage() {
  const { planId } = useParams();
  const router = useRouter();

  const [plan, setPlan] = useState(null);
  const [dependencies, setDependencies] = useState([]);
  const [conflicts, setConflicts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [error, setError] = useState(null);

  // Add Item Modal / State
  const [showAddItem, setShowAddItem] = useState(false);
  const [itemForm, setItemForm] = useState({
    name: "",
    resource_type: "task",
    resource_id: "",
    priority: "medium",
    estimated_duration: 30,
    required_capabilities: "",
  });

  const fetchPlanDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await planningService.getWorkPlan(planId);
      setPlan(data);

      const deps = await planningService.getPlanDependencies(planId);
      setDependencies(Array.isArray(deps) ? deps : []);
    } catch (err) {
      console.error("[PlanDetailPage] Load error:", err);
      setError(err.message || "Failed to load plan details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (planId) fetchPlanDetails();
  }, [planId]);

  const handleGenerate = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await planningService.generatePlan(planId, { planning_mode: plan?.planning_mode || "assisted" });
      await fetchPlanDetails();
    } catch (err) {
      setError(err.message || "Failed to generate plan");
    } finally {
      setActionLoading(false);
    }
  };

  const handleValidate = async () => {
    try {
      setActionLoading(true);
      setError(null);
      const res = await planningService.validatePlan(planId);
      setValidationResult(res);
    } catch (err) {
      setError(err.message || "Failed to validate plan");
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await planningService.activatePlan(planId);
      await fetchPlanDetails();
    } catch (err) {
      setError(err.message || "Failed to activate plan");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await planningService.pausePlan(planId);
      await fetchPlanDetails();
    } catch (err) {
      setError(err.message || "Failed to pause plan");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const caps = itemForm.required_capabilities
        ? itemForm.required_capabilities.split(",").map((s) => s.trim()).filter(Boolean)
        : [];
      await planningService.addPlanItem(planId, {
        name: itemForm.name,
        resource_type: itemForm.resource_type,
        resource_id: itemForm.resource_id || "task-auto",
        priority: itemForm.priority,
        estimated_duration: parseInt(itemForm.estimated_duration, 10),
        required_capabilities: caps,
      });
      setShowAddItem(false);
      setItemForm({
        name: "",
        resource_type: "task",
        resource_id: "",
        priority: "medium",
        estimated_duration: 30,
        required_capabilities: "",
      });
      await fetchPlanDetails();
    } catch (err) {
      setError(err.message || "Failed to add planning item");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !plan) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="h-8 bg-muted rounded w-1/3 animate-pulse" />
        <Card className="p-8 h-64 animate-pulse bg-card/60" />
      </div>
    );
  }

  const latestVersion = plan?.versions?.[0];
  const items = latestVersion?.items || [];
  const candidates = latestVersion?.candidates || [];

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Back button & Header */}
      <div>
        <Link href="/app/planning">
          <Button variant="ghost" size="sm" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Plans
          </Button>
        </Link>

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <CalendarRange className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">{plan?.name}</h1>
                <Badge variant={plan?.status === "active" ? "success" : "neutral"}>
                  {plan?.status?.toUpperCase()}
                </Badge>
                <Badge variant="outline" className="text-xs font-mono">
                  v{latestVersion?.version || 1}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">
                {plan?.description || "Work plan configuration and execution pipeline."}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleValidate}
              disabled={actionLoading}
              className="gap-2"
            >
              <Check className="w-4 h-4" />
              Validate
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              disabled={actionLoading}
              className="gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Generate Schedule
            </Button>
            {plan?.status !== "active" ? (
              <Button
                size="sm"
                onClick={handleActivate}
                disabled={actionLoading}
                className="gap-2"
              >
                <Play className="w-4 h-4" />
                Activate Plan
              </Button>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                onClick={handlePause}
                disabled={actionLoading}
                className="gap-2"
              >
                <Pause className="w-4 h-4" />
                Pause Plan
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Sub-nav Tabs */}
      <div className="flex border-b border-border/40 gap-2 overflow-x-auto text-sm pb-1">
        <Link href={`/app/planning/${planId}`}>
          <Button variant="ghost" size="sm" className="border-b-2 border-primary text-primary font-medium rounded-none">
            Overview
          </Button>
        </Link>
        <Link href={`/app/planning/${planId}/timeline`}>
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Timeline Gantt
          </Button>
        </Link>
        <Link href={`/app/planning/${planId}/dependencies`}>
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Dependencies ({dependencies.length})
          </Button>
        </Link>
        <Link href={`/app/planning/${planId}/resources`}>
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Resources
          </Button>
        </Link>
        <Link href={`/app/planning/${planId}/constraints`}>
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Constraints
          </Button>
        </Link>
        <Link href={`/app/planning/${planId}/scenarios`}>
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            What-If Scenarios
          </Button>
        </Link>
        <Link href={`/app/planning/${planId}/recommendations`}>
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Recommendations
          </Button>
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {validationResult && (
        <Card className={`p-4 border ${validationResult.is_valid ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : "bg-amber-500/10 border-amber-500/30 text-amber-400"}`}>
          <div className="flex items-start justify-between">
            <div>
              <div className="font-semibold text-sm flex items-center gap-2">
                {validationResult.is_valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                Plan Validation: {validationResult.is_valid ? "PASSED" : "FAILED / BLOCKED"}
              </div>
              {validationResult.is_stale && (
                <p className="text-xs text-amber-300 mt-1">
                  Stale Warning: {validationResult.stale_reasons?.join("; ") || "Plan state is out of sync."}
                </p>
              )}
              {validationResult.hard_violations?.length > 0 && (
                <div className="mt-2 space-y-1">
                  <span className="text-xs font-semibold">Hard Constraint Violations:</span>
                  {validationResult.hard_violations.map((v, idx) => (
                    <p key={idx} className="text-xs text-destructive">• {v}</p>
                  ))}
                </div>
              )}
            </div>
            <Button variant="ghost" size="sm" onClick={() => setValidationResult(null)} className="text-xs">
              Dismiss
            </Button>
          </div>
        </Card>
      )}

      {/* Main Grid: Work Items & Candidates */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Planning Items */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Layers className="w-5 h-5 text-primary" />
              Work Items ({items.length})
            </h2>
            <Button size="sm" onClick={() => setShowAddItem(true)} className="gap-1.5">
              <Plus className="w-4 h-4" />
              Add Work Item
            </Button>
          </div>

          {showAddItem && (
            <Card className="p-6 border-primary/30 bg-card/80">
              <form onSubmit={handleAddItem} className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Add Planned Work Item</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground">Item Name</label>
                    <Input
                      placeholder="e.g. Conduct security audit on API"
                      value={itemForm.name}
                      onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Resource Type</label>
                    <select
                      value={itemForm.resource_type}
                      onChange={(e) => setItemForm({ ...itemForm, resource_type: e.target.value })}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
                    >
                      <option value="task">Task</option>
                      <option value="workflow">Workflow</option>
                      <option value="agent_run">Agent Run</option>
                      <option value="agent_team_run">Agent Team Run</option>
                      <option value="approval">Human Approval</option>
                      <option value="evaluation">Evaluation</option>
                      <option value="simulation">Simulation</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground">Estimated Duration (minutes)</label>
                    <Input
                      type="number"
                      value={itemForm.estimated_duration}
                      onChange={(e) => setItemForm({ ...itemForm, estimated_duration: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Required Capabilities (comma separated)</label>
                    <Input
                      placeholder="e.g. security_review, python"
                      value={itemForm.required_capabilities}
                      onChange={(e) => setItemForm({ ...itemForm, required_capabilities: e.target.value })}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddItem(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" size="sm" disabled={actionLoading}>
                    Add Item
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {items.length === 0 ? (
            <Card className="p-8 text-center text-muted-foreground border-dashed">
              No items in this version. Click "Add Work Item" to define tasks, workflows, or agent executions.
            </Card>
          ) : (
            <div className="space-y-3">
              {items.map((it) => (
                <Card key={it.id} className="p-4 flex items-center justify-between hover:border-border transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-foreground text-sm">{it.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {it.resource_type}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {it.priority}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Est. Duration: {it.estimated_duration || 30}m</span>
                      {it.required_capabilities?.length > 0 && (
                        <span>Caps: {it.required_capabilities.join(", ")}</span>
                      )}
                      <span>Status: {it.status}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Schedule Candidates */}
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Schedule Candidates ({candidates.length})
          </h2>

          {candidates.length === 0 ? (
            <Card className="p-8 text-center text-muted-foreground border-dashed">
              No candidates generated yet. Click "Generate Schedule" to compute optimal candidate sequences.
            </Card>
          ) : (
            <div className="space-y-4">
              {candidates.map((cand, idx) => (
                <Card key={cand.id || idx} className="p-5 space-y-3 bg-card/80 border-border/80">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-sm text-foreground">{cand.name}</h4>
                      <span className="text-xs text-muted-foreground">Candidate #{idx + 1}</span>
                    </div>
                    <Badge variant="info" className="text-xs">
                      {cand.estimated_duration ? `${cand.estimated_duration}m` : "Duration N/A"}
                    </Badge>
                  </div>

                  <div className="text-xs space-y-1 text-muted-foreground border-t border-border/40 pt-2">
                    <div>Estimated Cost: ${cand.estimated_cost?.toFixed(2) || "0.00"}</div>
                    <div>Allocations: {Object.keys(cand.resource_allocations || {}).length} resources assigned</div>
                  </div>

                  {cand.assumptions?.length > 0 && (
                    <div className="text-xs bg-muted/30 p-2.5 rounded border border-border/40 space-y-1">
                      <span className="font-medium text-foreground">Assumptions:</span>
                      {cand.assumptions.map((asm, i) => (
                        <p key={i} className="text-muted-foreground">• {asm}</p>
                      ))}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

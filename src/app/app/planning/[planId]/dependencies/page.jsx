"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { planningService } from "@/services/planning";
import {
  Network,
  ArrowLeft,
  Plus,
  AlertTriangle,
  CheckCircle2,
  GitBranch,
} from "lucide-react";

export default function PlanDependenciesPage() {
  const { planId } = useParams();

  const [plan, setPlan] = useState(null);
  const [dependencies, setDependencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const [depForm, setDepForm] = useState({
    predecessor_item_id: "",
    successor_item_id: "",
    dependency_type: "finish_to_start",
    lag: 0,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const planData = await planningService.getWorkPlan(planId);
      setPlan(planData);
      const deps = await planningService.getPlanDependencies(planId);
      setDependencies(Array.isArray(deps) ? deps : []);
    } catch (err) {
      setError(err.message || "Failed to load dependencies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (planId) loadData();
  }, [planId]);

  const handleAddDependency = async (e) => {
    e.preventDefault();
    if (!depForm.predecessor_item_id || !depForm.successor_item_id) {
      setError("Please select both predecessor and successor items.");
      return;
    }
    if (depForm.predecessor_item_id === depForm.successor_item_id) {
      setError("An item cannot depend on itself (self-cycle forbidden).");
      return;
    }

    try {
      setActionLoading(true);
      setError(null);
      await planningService.addPlanDependency(planId, {
        predecessor_item_id: depForm.predecessor_item_id,
        successor_item_id: depForm.successor_item_id,
        dependency_type: depForm.dependency_type,
        lag: parseInt(depForm.lag || 0, 10),
      });
      await loadData();
      setDepForm({
        predecessor_item_id: "",
        successor_item_id: "",
        dependency_type: "finish_to_start",
        lag: 0,
      });
    } catch (err) {
      setError(err.message || "Failed to add dependency");
    } finally {
      setActionLoading(false);
    }
  };

  const items = plan?.versions?.[0]?.items || [];
  const itemMap = Object.fromEntries(items.map((it) => [it.id, it.name]));

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      <div>
        <Link href={`/app/planning/${planId}`}>
          <Button variant="ghost" size="sm" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Plan Overview
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
            <Network className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Work Dependencies & Cycle Guard
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Strict acyclic precedence graph. Circular dependencies are deterministically rejected.
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

      {/* Add Dependency Form */}
      <Card className="p-6">
        <h3 className="font-semibold text-sm text-foreground mb-4">Add Dependency Link</h3>
        <form onSubmit={handleAddDependency} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-xs text-muted-foreground">Predecessor (Runs First)</label>
            <select
              value={depForm.predecessor_item_id}
              onChange={(e) => setDepForm({ ...depForm, predecessor_item_id: e.target.value })}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
              required
            >
              <option value="">Select Predecessor...</option>
              {items.map((it) => (
                <option key={it.id} value={it.id}>
                  {it.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-muted-foreground">Successor (Depends On It)</label>
            <select
              value={depForm.successor_item_id}
              onChange={(e) => setDepForm({ ...depForm, successor_item_id: e.target.value })}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
              required
            >
              <option value="">Select Successor...</option>
              {items.map((it) => (
                <option key={it.id} value={it.id}>
                  {it.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-muted-foreground">Dependency Type</label>
            <select
              value={depForm.dependency_type}
              onChange={(e) => setDepForm({ ...depForm, dependency_type: e.target.value })}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
            >
              <option value="finish_to_start">Finish to Start</option>
              <option value="start_to_start">Start to Start</option>
              <option value="finish_to_finish">Finish to Finish</option>
              <option value="blocks">Blocks</option>
              <option value="requires">Requires</option>
            </select>
          </div>

          <div>
            <Button type="submit" disabled={actionLoading} className="w-full gap-2">
              <Plus className="w-4 h-4" />
              Add Dependency
            </Button>
          </div>
        </form>
      </Card>

      {/* Dependencies List */}
      <Card className="p-6">
        <h3 className="font-semibold text-sm text-foreground mb-4">
          Configured Dependencies ({dependencies.length})
        </h3>

        {dependencies.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground border-dashed border rounded-lg">
            No dependencies recorded. Tasks will run independently according to available resource concurrency.
          </div>
        ) : (
          <div className="space-y-3">
            {dependencies.map((dep) => (
              <div
                key={dep.id}
                className="p-3.5 rounded-lg bg-card/60 border border-border/40 flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium text-foreground">
                    {itemMap[dep.predecessor_item_id] || dep.predecessor_item_id}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {dep.dependency_type}
                  </Badge>
                  <span className="text-muted-foreground">➔</span>
                  <span className="font-medium text-foreground">
                    {itemMap[dep.successor_item_id] || dep.successor_item_id}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">Lag: {dep.lag}m</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

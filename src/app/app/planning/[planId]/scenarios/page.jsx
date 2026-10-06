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
  Sliders,
  ArrowLeft,
  Plus,
  Play,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
} from "lucide-react";

export default function PlanScenariosPage() {
  const { planId } = useParams();

  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const [showAddScenario, setShowAddScenario] = useState(false);
  const [scenarioForm, setScenarioForm] = useState({
    name: "",
    description: "",
    duration_multiplier: "1.5",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await planningService.getWorkPlan(planId);
      setPlan(data);
    } catch (err) {
      setError(err.message || "Failed to load scenarios");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (planId) loadData();
  }, [planId]);

  const handleCreateScenario = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      await planningService.createScenario({
        work_plan_id: planId,
        name: scenarioForm.name,
        description: scenarioForm.description || null,
        modifications: {
          duration_multiplier: parseFloat(scenarioForm.duration_multiplier || 1.0),
        },
      });
      setShowAddScenario(false);
      setScenarioForm({ name: "", description: "", duration_multiplier: "1.5" });
      await loadData();
    } catch (err) {
      setError(err.message || "Failed to create scenario");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunScenario = async (scenarioId) => {
    try {
      setActionLoading(true);
      await planningService.runScenario(scenarioId);
      await loadData();
    } catch (err) {
      setError(err.message || "Failed to run scenario");
    } finally {
      setActionLoading(false);
    }
  };

  const scenarios = plan?.scenarios || [];

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      <div>
        <Link href={`/app/planning/${planId}`}>
          <Button variant="ghost" size="sm" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Plan Overview
          </Button>
        </Link>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Sliders className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                What-If Planning Scenarios
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Simulate hypothetical deadline changes, resource dropouts, or cost changes without modifying production plans.
              </p>
            </div>
          </div>

          <Button size="sm" onClick={() => setShowAddScenario(true)} className="gap-2">
            <Plus className="w-4 h-4" />
            New What-If Scenario
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {showAddScenario && (
        <Card className="p-6 border-primary/40 bg-card/80">
          <form onSubmit={handleCreateScenario} className="space-y-4">
            <h3 className="font-semibold text-sm text-foreground">Define What-If Scenario</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">Scenario Name</label>
                <Input
                  placeholder="e.g. 50% Duration Overrun Simulation"
                  value={scenarioForm.name}
                  onChange={(e) => setScenarioForm({ ...scenarioForm, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Duration Multiplier (e.g. 1.5 = +50%)</label>
                <Input
                  type="number"
                  step="0.1"
                  value={scenarioForm.duration_multiplier}
                  onChange={(e) => setScenarioForm({ ...scenarioForm, duration_multiplier: e.target.value })}
                  required
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Hypothesis / Description</label>
              <Input
                placeholder="What if tasks take 50% longer due to unforeseen blockers?"
                value={scenarioForm.description}
                onChange={(e) => setScenarioForm({ ...scenarioForm, description: e.target.value })}
              />
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddScenario(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={actionLoading}>
                Save Scenario
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Scenarios List */}
      <div className="space-y-4">
        {scenarios.length === 0 ? (
          <Card className="p-8 text-center text-muted-foreground border-dashed">
            No what-if scenarios defined. Create a scenario to test alternative timelines or capacity limits safely.
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {scenarios.map((sc) => {
              const comp = sc.comparison?.comparison || [];
              const hasRun = sc.simulation_results && Object.keys(sc.simulation_results).length > 0;

              return (
                <Card key={sc.id} className="p-6 space-y-4 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-base text-foreground">{sc.name}</h3>
                      <Badge variant={hasRun ? "success" : "neutral"} className="text-xs">
                        {hasRun ? "Simulated" : "Draft"}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{sc.description || "No hypothesis entered."}</p>

                    {hasRun && comp.length > 0 && (
                      <div className="pt-3 border-t border-border/40 space-y-2">
                        <span className="text-xs font-semibold text-foreground">Simulated Impact:</span>
                        {comp.map((c, i) => (
                          <div key={i} className="text-xs bg-muted/30 p-2.5 rounded border border-border/40 space-y-1">
                            <span className="font-medium text-foreground">{c.name}</span>
                            <div className="flex items-center justify-between text-muted-foreground">
                              <span>Duration: {c.duration_minutes}m</span>
                              <span>Cost: ${c.cost_usd?.toFixed(2) || "0.00"}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="pt-4 border-t border-border/40 flex items-center justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={actionLoading}
                      onClick={() => handleRunScenario(sc.id)}
                      className="gap-2"
                    >
                      <Play className="w-3.5 h-3.5" />
                      Run Simulation
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

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
  ShieldCheck,
  AlertTriangle,
  Lock,
} from "lucide-react";

export default function PlanConstraintsPage() {
  const { planId } = useParams();

  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await planningService.getWorkPlan(planId);
        setPlan(data);
      } catch (err) {
        setError(err.message || "Failed to load constraints");
      } finally {
        setLoading(false);
      }
    }
    if (planId) loadData();
  }, [planId]);

  const latestVersion = plan?.versions?.[0];
  const constraints = latestVersion?.constraints || [];

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
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Planning Constraints & Guardrails
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Hard security and operational boundaries cannot be overridden or traded off by optimization.
            </p>
          </div>
        </div>
      </div>

      {/* Precedence Notice */}
      <Card className="p-4 bg-muted/20 border-border/60">
        <div className="flex items-start gap-3">
          <Lock className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-semibold text-foreground">Constraint Precedence Architecture:</span>
            <p className="text-muted-foreground">
              System Security ➔ Governance ➔ Tenant Isolation ➔ RBAC ➔ Safety/HITL ➔ Hard Planning Constraints ➔ Resource Limits ➔ Soft Preferences.
            </p>
          </div>
        </div>
      </Card>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Constraints List */}
      <div className="space-y-4">
        <h3 className="font-semibold text-base text-foreground">Active Plan Constraints ({constraints.length})</h3>

        {constraints.length === 0 ? (
          <Card className="p-8 text-center text-muted-foreground border-dashed">
            No custom constraints defined for this version. System security, governance policies, and dependency rules still apply by default.
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {constraints.map((c) => (
              <Card key={c.id} className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs font-mono uppercase">
                    {c.constraint_type}
                  </Badge>
                  <Badge variant={c.hard_constraint ? "destructive" : "secondary"} className="text-xs">
                    {c.hard_constraint ? "HARD" : "SOFT"}
                  </Badge>
                </div>
                <div className="text-xs font-mono bg-muted/30 p-2.5 rounded border border-border/40 overflow-x-auto">
                  {JSON.stringify(c.configuration, null, 2)}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

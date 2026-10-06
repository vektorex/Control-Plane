"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { planningService } from "@/services/planning";
import {
  CalendarRange,
  ArrowLeft,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function PlanTimelinePage() {
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
        setError(err.message || "Failed to load timeline data");
      } finally {
        setLoading(false);
      }
    }
    if (planId) loadData();
  }, [planId]);

  const latestVersion = plan?.versions?.[0];
  const items = latestVersion?.items || [];
  const candidate = latestVersion?.candidates?.[0];
  const schedule = candidate?.schedule || {};

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
            <CalendarRange className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Timeline & Execution Schedule
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Gantt-style timeline visualization of planned sequence, start/end windows, and durations.
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

      {loading ? (
        <Card className="p-12 animate-pulse h-64 bg-card/60" />
      ) : items.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground border-dashed">
          No work items in this plan to display on the timeline.
        </Card>
      ) : (
        <Card className="p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-border/40 pb-4">
            <div className="space-y-1">
              <h3 className="font-semibold text-base text-foreground">
                Active Candidate Schedule: {candidate?.name || "Baseline"}
              </h3>
              <p className="text-xs text-muted-foreground">
                Estimated Duration: {candidate?.estimated_duration || 60} minutes
              </p>
            </div>
            <Badge variant="outline" className="text-xs font-mono">
              Factual Estimate
            </Badge>
          </div>

          {/* Timeline visualization items */}
          <div className="space-y-4">
            {items.map((it, idx) => {
              const itemSchedule = schedule[it.id] || {};
              const dur = it.estimated_duration || 30;
              // Bar width relative to max 120 mins
              const widthPct = Math.min(100, Math.max(20, (dur / 120) * 100));

              return (
                <div key={it.id} className="space-y-1.5 p-3 rounded-lg bg-card/60 border border-border/40">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-foreground">{it.name}</span>
                    <span className="text-muted-foreground font-mono">{dur}m</span>
                  </div>

                  <div className="w-full bg-muted/40 h-6 rounded-md overflow-hidden relative flex items-center">
                    <div
                      className="bg-primary/80 hover:bg-primary h-full rounded-md flex items-center px-2 text-[10px] text-primary-foreground font-medium transition-all"
                      style={{ width: `${widthPct}%` }}
                    >
                      {it.resource_type} • {itemSchedule.resource_id || "unassigned"}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                    <span>Planned Start: {itemSchedule.start ? new Date(itemSchedule.start).toLocaleTimeString() : "TBD"}</span>
                    <span>Planned End: {itemSchedule.end ? new Date(itemSchedule.end).toLocaleTimeString() : "TBD"}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { planningService } from "@/services/planning";
import {
  Sparkles,
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react";

export default function PlanRecommendationsPage() {
  const { planId } = useParams();

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await planningService.listRecommendations(planId);
        setRecommendations(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || "Failed to load recommendations");
      } finally {
        setLoading(false);
      }
    }
    if (planId) loadData();
  }, [planId]);

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
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Advisory Planning Recommendations
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Evidence-based next action suggestions. Recommendations never bypass governance or execute autonomously.
            </p>
          </div>
        </div>
      </div>

      {/* Advisory Banner */}
      <Card className="p-4 bg-muted/20 border-border/60">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <p className="text-xs text-muted-foreground">
            Recommendations are suggestions generated from capability mismatches, active blockers, and duration overruns. Authorized humans must review and explicitly execute any structural plan changes.
          </p>
        </div>
      </Card>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <Card key={i} className="p-6 h-32 animate-pulse bg-card/60" />
          ))}
        </div>
      ) : recommendations.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground border-dashed">
          No active recommendations for this plan. Generate a schedule or validate the plan to trigger recommendation checks.
        </Card>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <Card key={rec.id} className="p-6 space-y-3 hover:border-primary/30 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs font-mono uppercase">
                      {rec.recommendation_type}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      {rec.status}
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-base text-foreground mt-1">{rec.description}</h3>
                </div>
              </div>

              <div className="text-xs text-muted-foreground space-y-1.5 pt-2 border-t border-border/40">
                <div>
                  <strong className="text-foreground">Reason:</strong> {rec.reason}
                </div>
                {rec.risk && (
                  <div>
                    <strong className="text-amber-400">Risk Assessment:</strong> {rec.risk}
                  </div>
                )}
                {rec.assumptions?.length > 0 && (
                  <div>
                    <strong className="text-foreground">Assumptions:</strong> {rec.assumptions.join("; ")}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

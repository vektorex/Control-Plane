"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { planningService } from "@/services/planning";
import {
  Users2,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Layers,
  Activity,
} from "lucide-react";

export default function PlanResourcesPage() {
  const { planId } = useParams();

  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await planningService.getPlanResources(planId);
        setResources(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || "Failed to load plan resources");
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
            <Users2 className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Plan Resources & Capability Mapping
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Available execution agents, teams, workflows, and humans with verified suitability constraints.
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((i) => (
            <Card key={i} className="p-6 h-48 animate-pulse bg-card/60" />
          ))}
        </div>
      ) : resources.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground border-dashed">
          No resources registered in this workspace. Visit the Resources section to register agents and capabilities.
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resources.map((res) => (
            <Card key={res.id} className="p-6 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs uppercase font-mono">
                    {res.resource_type}
                  </Badge>
                  <Badge variant={res.status === "active" ? "success" : "neutral"} className="text-xs">
                    {res.status}
                  </Badge>
                </div>

                <div>
                  <h3 className="font-semibold text-base text-foreground">{res.name}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                    {res.description || "No resource description."}
                  </p>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-border/40">
                  <span className="text-xs font-semibold text-foreground">Declared Capabilities:</span>
                  <div className="flex flex-wrap gap-1">
                    {(res.capabilities || []).map((cap, i) => (
                      <Badge key={i} variant="secondary" className="text-[10px]">
                        {cap}
                      </Badge>
                    ))}
                    {(!res.capabilities || res.capabilities.length === 0) && (
                      <span className="text-xs text-muted-foreground">General</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border/40 flex items-center justify-between text-xs text-muted-foreground">
                <span>Ref: {res.resource_ref?.slice(0, 8)}...</span>
                <Link href={`/app/resources/${res.id}/capacity`}>
                  <Button variant="ghost" size="sm" className="text-xs">
                    Check Capacity
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

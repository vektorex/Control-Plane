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
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  Cpu,
  Layers,
  Lock,
} from "lucide-react";

export default function ResourceDetailPage() {
  const { resourceId } = useParams();

  const [resource, setResource] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await planningService.getResource(resourceId);
        setResource(data);
      } catch (err) {
        setError(err.message || "Failed to load resource");
      } finally {
        setLoading(false);
      }
    }
    if (resourceId) loadData();
  }, [resourceId]);

  if (loading && !resource) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <div className="h-8 bg-muted rounded w-1/3 animate-pulse" />
        <Card className="p-8 h-64 animate-pulse bg-card/60" />
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6 max-w-4xl mx-auto">
      <div>
        <Link href="/app/resources">
          <Button variant="ghost" size="sm" className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Resources
          </Button>
        </Link>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Users2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">{resource?.name}</h1>
                <Badge variant={resource?.status === "active" ? "success" : "neutral"}>
                  {resource?.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">
                Type: {resource?.resource_type} • Reference: {resource?.resource_ref}
              </p>
            </div>
          </div>

          <Link href={`/app/resources/${resourceId}/capacity`}>
            <Button size="sm" className="gap-1.5">
              View Capacity
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <Card className="p-6 space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Description</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {resource?.description || "No description recorded for this resource."}
          </p>
        </div>

        <div className="pt-4 border-t border-border/40 space-y-2">
          <h3 className="text-sm font-semibold text-foreground">Capabilities & Suitability</h3>
          <div className="flex flex-wrap gap-1.5">
            {(resource?.capabilities || []).map((c, i) => (
              <Badge key={i} variant="secondary">
                {c}
              </Badge>
            ))}
          </div>
          <p className="text-xs text-muted-foreground pt-1">
            * Note: Capability declarations describe suitability only. Authorization and permissions remain governed by RBAC, Governance, and HITL policies.
          </p>
        </div>

        <div className="pt-4 border-t border-border/40 space-y-2">
          <h3 className="text-sm font-semibold text-foreground">Availability Policy</h3>
          <div className="text-xs font-mono bg-muted/30 p-3 rounded border border-border/40 overflow-x-auto">
            {JSON.stringify(resource?.availability_policy || {}, null, 2)}
          </div>
        </div>
      </Card>
    </div>
  );
}

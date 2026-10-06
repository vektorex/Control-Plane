"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { planningService } from "@/services/planning";
import {
  Users2,
  RefreshCw,
  Gauge,
  AlertTriangle,
  Layers,
  ShieldCheck,
  Lock,
} from "lucide-react";

export default function CapacityWorkloadPage() {
  const [workloads, setWorkloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchWorkloads = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await planningService.getCapacityWorkload();
      setWorkloads(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load workload distributions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkloads();
  }, []);

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <Users2 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Resource Workload Distribution
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Factual allocation of tasks across agents, teams, workflows, and humans.
              </p>
            </div>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={fetchWorkloads} disabled={loading} className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Sub-nav */}
      <div className="flex border-b border-border/40 gap-2 text-sm pb-1">
        <Link href="/app/capacity/forecast">
          <Button variant="ghost" size="sm" className="text-muted-foreground rounded-none">
            Forecast Overview
          </Button>
        </Link>
        <Link href="/app/capacity/workload">
          <Button variant="ghost" size="sm" className="border-b-2 border-primary text-primary font-medium rounded-none">
            Resource Workload
          </Button>
        </Link>
      </div>

      {/* Safety & Anti-Ranking Notice */}
      <Card className="p-4 bg-muted/20 border-border/60">
        <div className="flex items-start gap-3">
          <Lock className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-semibold text-foreground">Anti-Surveillance & Anti-Ranking Policy:</span>
            <p className="text-muted-foreground">
              Workload metrics display planned allocations and concurrency commitments. Subjective productivity rankings, employee leaderboards, and scoring of human individuals are strictly forbidden.
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

      {/* Workload Table */}
      <Card className="p-6">
        <h3 className="font-semibold text-base text-foreground mb-4">
          Allocated Workload by Resource ({workloads.length})
        </h3>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-muted/40 rounded animate-pulse" />
            ))}
          </div>
        ) : workloads.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground border-dashed border rounded-lg">
            No resources or workloads found in this workspace.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted-foreground uppercase border-b border-border/40">
                <tr>
                  <th className="pb-3 font-semibold">Resource</th>
                  <th className="pb-3 font-semibold">Type</th>
                  <th className="pb-3 font-semibold">Scheduled Workload</th>
                  <th className="pb-3 font-semibold">Reserved Units</th>
                  <th className="pb-3 font-semibold">Remaining Capacity</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {workloads.map((w) => (
                  <tr key={w.resource_id} className="hover:bg-muted/20 transition-colors">
                    <td className="py-3.5 font-medium text-foreground">{w.resource_name}</td>
                    <td className="py-3.5">
                      <Badge variant="outline" className="text-xs font-mono uppercase">
                        {w.resource_type}
                      </Badge>
                    </td>
                    <td className="py-3.5 font-mono text-xs">{w.scheduled_workload} units</td>
                    <td className="py-3.5 font-mono text-xs">{w.reserved_capacity} units</td>
                    <td className="py-3.5 font-mono text-xs text-emerald-400">
                      {w.remaining_capacity} units
                    </td>
                    <td className="py-3.5 text-right">
                      <Link href={`/app/resources/${w.resource_id}/capacity`}>
                        <Button variant="ghost" size="sm" className="text-xs">
                          Inspect
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

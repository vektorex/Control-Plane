"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { planningService } from "@/services/planning";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  CalendarRange,
  Plus,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Layers,
  Activity,
  CheckCircle2,
  Sliders,
  Users2,
  Gauge,
} from "lucide-react";

export default function PlanningPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState(null);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter !== "ALL") params.status = statusFilter.toLowerCase();
      const data = await planningService.listWorkPlans(params);
      setPlans(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[PlanningPage] Error fetching plans:", err);
      setError(err.message || "Failed to load work plans");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, [activeWorkspace, statusFilter]);

  const filteredPlans = plans.filter((p) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      p.name?.toLowerCase().includes(query) ||
      p.description?.toLowerCase().includes(query) ||
      p.status?.toLowerCase().includes(query)
    );
  });

  const activeCount = plans.filter((p) => p.status === "active").length;
  const draftCount = plans.filter((p) => p.status === "draft").length;
  const proposedCount = plans.filter((p) => p.status === "proposed").length;
  const pausedCount = plans.filter((p) => p.status === "paused").length;

  const getStatusBadge = (status) => {
    switch (status) {
      case "active":
        return <Badge variant="success">Active</Badge>;
      case "proposed":
        return <Badge variant="warning">Proposed</Badge>;
      case "approved":
        return <Badge variant="info">Approved</Badge>;
      case "paused":
        return <Badge variant="secondary">Paused</Badge>;
      case "completed":
        return <Badge variant="neutral">Completed</Badge>;
      default:
        return <Badge variant="neutral">{status || "Draft"}</Badge>;
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <CalendarRange className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Work Planning & Resource Optimization
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Evidence-backed sequencing, capacity analysis, dependency scheduling, and isolated what-if scenarios.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchPlans}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Link href="/app/planning/new">
            <Button size="sm" className="gap-2">
              <Plus className="w-4 h-4" />
              New Work Plan
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Plans"
          value={activeCount}
          icon={Activity}
          description="Currently sequencing work"
        />
        <StatCard
          title="Proposed Plans"
          value={proposedCount}
          icon={Clock}
          description="Awaiting review or validation"
        />
        <StatCard
          title="Draft Plans"
          value={draftCount}
          icon={Layers}
          description="In design / preparation"
        />
        <StatCard
          title="Paused / Completed"
          value={pausedCount}
          icon={ShieldCheck}
          description="Execution held or concluded"
        />
      </div>

      {/* Filters & Search */}
      <Card className="p-4 bg-card/60 backdrop-blur-sm border-border/60">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search plans by name, description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
            {["ALL", "ACTIVE", "PROPOSED", "DRAFT", "PAUSED", "COMPLETED"].map((st) => (
              <Button
                key={st}
                size="sm"
                variant={statusFilter === st ? "primary" : "ghost"}
                onClick={() => setStatusFilter(st)}
                className="text-xs capitalize"
              >
                {st.toLowerCase()}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* Plan List */}
      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 space-y-4 animate-pulse">
              <div className="h-6 bg-muted rounded w-3/4" />
              <div className="h-4 bg-muted rounded w-full" />
              <div className="h-10 bg-muted rounded w-full" />
            </Card>
          ))}
        </div>
      ) : filteredPlans.length === 0 ? (
        <Card className="p-12 text-center space-y-4 border-dashed">
          <div className="w-12 h-12 rounded-2xl bg-muted/50 mx-auto flex items-center justify-center text-muted-foreground">
            <CalendarRange className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-lg text-foreground">No Work Plans Found</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              {searchQuery
                ? "No work plans match your search query."
                : "Create your first work plan to sequence tasks, optimize resources, and evaluate capacity."}
            </p>
          </div>
          {!searchQuery && (
            <Link href="/app/planning/new">
              <Button size="sm" className="gap-2 mt-2">
                <Plus className="w-4 h-4" />
                Create Work Plan
              </Button>
            </Link>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlans.map((plan) => (
            <Card
              key={plan.id}
              className="p-6 flex flex-col justify-between hover:border-primary/40 transition-all duration-200 group relative"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                    Mode: {plan.planning_mode || "assisted"}
                  </span>
                  {getStatusBadge(plan.status)}
                </div>

                <div>
                  <h3 className="font-semibold text-lg text-foreground group-hover:text-primary transition-colors line-clamp-1">
                    {plan.name}
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                    {plan.description || "No plan description provided."}
                  </p>
                </div>
              </div>

              <div className="pt-6 mt-6 border-t border-border/40 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  Created {new Date(plan.created_at).toLocaleDateString()}
                </span>
                <Link href={`/app/planning/${plan.id}`}>
                  <Button variant="ghost" size="sm" className="gap-1.5 text-xs group-hover:text-primary">
                    View Plan
                    <ArrowRight className="w-3.5 h-3.5" />
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

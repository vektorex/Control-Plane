"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { outcomeService } from "@/services/outcomes";
import { useWorkspace } from "@/lib/workspaceContext";
import {
  Target,
  Plus,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Award,
  CheckCircle2,
  Calendar,
  Layers,
  Activity,
  Flame,
} from "lucide-react";

export default function ObjectivesPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [objectives, setObjectives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [error, setError] = useState(null);

  const fetchObjectives = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter !== "ALL") params.status = statusFilter.toLowerCase();
      if (typeFilter !== "ALL") params.objective_type = typeFilter.toLowerCase();
      const data = await outcomeService.listObjectives(params);
      setObjectives(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[ObjectivesPage] Error fetching objectives:", err);
      setError(err.message || "Failed to load objectives");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObjectives();
  }, [activeWorkspace, statusFilter, typeFilter]);

  const filteredObjectives = objectives.filter((obj) => {
    const q = searchQuery.toLowerCase();
    return (
      obj.name?.toLowerCase().includes(q) ||
      obj.description?.toLowerCase().includes(q) ||
      obj.objective_type?.toLowerCase().includes(q)
    );
  });

  const activeCount = objectives.filter((o) => o.status === "active").length;
  const completedCount = objectives.filter((o) => o.status === "completed").length;
  const atRiskCount = objectives.filter((o) => o.status === "at_risk").length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Target className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">Strategic Objectives</h1>
              <p className="text-sm text-slate-400">
                Track business, product, and engineering objectives connected to deliverables and work execution.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchObjectives}
            disabled={loading}
            className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 text-slate-300"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Link href="/app/objectives/new">
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/20">
              <Plus className="w-4 h-4 mr-2" />
              New Objective
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Objectives"
          value={objectives.length}
          icon={Target}
          description="Managed strategic intents"
        />
        <StatCard
          title="Active Objectives"
          value={activeCount}
          icon={Activity}
          description="In active execution"
        />
        <StatCard
          title="At Risk"
          value={atRiskCount}
          icon={AlertTriangle}
          description="Blocked or overdue items"
        />
        <StatCard
          title="Completed"
          value={completedCount}
          icon={CheckCircle2}
          description="Satisfied & achieved"
        />
      </div>

      {/* Filters and Search */}
      <Card className="p-4 bg-slate-900/60 border-slate-800/80 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
            <Input
              placeholder="Search objectives by name, description, or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-slate-950/60 border-slate-800 text-slate-200 placeholder:text-slate-500 w-full"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="at_risk">At Risk</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="archived">Archived</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Types</option>
              <option value="business">Business</option>
              <option value="product">Product</option>
              <option value="engineering">Engineering</option>
              <option value="research">Research</option>
              <option value="operations">Operations</option>
              <option value="security">Security</option>
              <option value="compliance">Compliance</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Objectives Grid */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
      ) : filteredObjectives.length === 0 ? (
        <Card className="p-12 text-center bg-slate-900/40 border-slate-800/60">
          <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-300 mb-2">No objectives found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
            Create an objective to connect AI agent runs, workflows, and deliverables to intended business outcomes.
          </p>
          <Link href="/app/objectives/new">
            <Button size="sm" className="bg-indigo-600 hover:bg-indigo-500 text-white">
              <Plus className="w-4 h-4 mr-2" />
              Create First Objective
            </Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredObjectives.map((obj) => (
            <Card
              key={obj.id}
              onClick={() => router.push(`/app/objectives/${obj.id}`)}
              className="group p-6 bg-slate-900/40 hover:bg-slate-900/80 border-slate-800/80 hover:border-indigo-500/40 transition-all duration-200 cursor-pointer flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs uppercase font-mono tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        {obj.objective_type}
                      </span>
                      <span className="text-xs font-mono text-slate-500 capitalize">
                        {obj.priority} priority
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-indigo-400 transition-colors">
                      {obj.name}
                    </h3>
                  </div>

                  <Badge
                    variant={
                      obj.status === "completed"
                        ? "success"
                        : obj.status === "at_risk"
                        ? "destructive"
                        : obj.status === "active"
                        ? "info"
                        : "secondary"
                    }
                    className="capitalize"
                  >
                    {obj.status.replace("_", " ")}
                  </Badge>
                </div>

                <p className="text-sm text-slate-400 line-clamp-2">
                  {obj.description || "No description provided."}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    {obj.target_at ? new Date(obj.target_at).toLocaleDateString() : "No target date"}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-indigo-400 group-hover:translate-x-1 transition-transform">
                  <span>View Details</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

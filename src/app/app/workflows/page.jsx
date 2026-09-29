"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { workflowService } from "@/services/workflows";
import { useWorkspace } from "@/lib/workspaceContext";
import { TemplateGallery } from "@/components/features/workflows/TemplateGallery";
import { CreateWorkflowModal } from "@/components/features/workflows/CreateWorkflowModal";
import { RunWorkflowModal } from "@/components/features/workflows/RunWorkflowModal";
import {
  Workflow,
  Plus,
  Play,
  Copy,
  Trash2,
  Edit,
  Search,
  RefreshCw,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export default function WorkflowsPage() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspace();

  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [runningWorkflow, setRunningWorkflow] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState(null);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = statusFilter !== "ALL" ? { status: statusFilter.toLowerCase() } : {};
      const res = await workflowService.listWorkflows(params);
      setWorkflows(res?.workflows || []);
    } catch (err) {
      console.error("[WorkflowsPage] Error fetching workflows:", err);
      setError(err.message || "Failed to load workflows");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, [activeWorkspace?.id, statusFilter]);

  const handleDuplicate = async (wf) => {
    try {
      setActionLoading(wf.id);
      const duplicated = await workflowService.duplicateWorkflow(wf.id);
      setWorkflows((prev) => [duplicated, ...prev]);
    } catch (err) {
      console.error("[WorkflowsPage] Duplication error:", err);
      setError(err.message || "Failed to duplicate workflow");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (wf) => {
    if (!confirm(`Are you sure you want to delete workflow "${wf.name}"?`)) return;
    try {
      setActionLoading(wf.id);
      await workflowService.deleteWorkflow(wf.id);
      setWorkflows((prev) => prev.filter((item) => item.id !== wf.id));
    } catch (err) {
      console.error("[WorkflowsPage] Deletion error:", err);
      setError(err.message || "Failed to delete workflow");
    } finally {
      setActionLoading(null);
    }
  };

  const filteredWorkflows = workflows.filter((wf) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      wf.name.toLowerCase().includes(q) ||
      (wf.description && wf.description.toLowerCase().includes(q)) ||
      wf.slug.toLowerCase().includes(q)
    );
  });

  const publishedCount = workflows.filter((w) => w.status === "published").length;
  const draftCount = workflows.filter((w) => w.status === "draft").length;
  const totalRunsCount = workflows.reduce((acc, w) => acc + (w.runs_count || 0), 0);

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Workflow className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100 tracking-tight">AI Workflows</h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Build, validate, publish, and orchestrate deterministic multi-step pipelines
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchWorkflows}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateOpen(true)}
            className="gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Workflow</span>
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Workflows"
          value={workflows.length}
          icon={Layers}
          trend={{ value: `${draftCount} drafts`, isPositive: true }}
        />
        <StatCard
          label="Published Pipelines"
          value={publishedCount}
          icon={CheckCircle2}
          trend={{ value: "Version immutable", isPositive: true }}
        />
        <StatCard
          label="Total Runs Executed"
          value={totalRunsCount}
          icon={Play}
          trend={{ value: "Orchestrated", isPositive: true }}
        />
        <StatCard
          label="Built-in Templates"
          value="4"
          icon={Sparkles}
          trend={{ value: "Instant install", isPositive: true }}
        />
      </div>

      {/* Template Gallery Section */}
      <div className="pt-2">
        <TemplateGallery
          onTemplateInstalled={(installedWf) => {
            setWorkflows((prev) => [installedWf, ...prev]);
          }}
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-800/80">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          {["ALL", "PUBLISHED", "DRAFT", "ARCHIVED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search workflows by name or slug..."
            className="pl-9 text-xs"
          />
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Workflow List Cards */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
          <p className="text-sm">Loading workflows...</p>
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <Card className="p-12 text-center bg-slate-900/40 border-slate-800 border-dashed">
          <Workflow className="w-10 h-10 mx-auto text-slate-400 mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No workflows found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-4">
            {searchQuery
              ? "No workflows match your search query."
              : "Get started by creating a new custom workflow or installing one of the built-in templates above."}
          </p>
          <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            Create First Workflow
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkflows.map((wf) => {
            const isPublished = wf.status === "published";
            const isArchived = wf.status === "archived";
            const isActioning = actionLoading === wf.id;
            const stepsCount = wf.steps?.length || 0;

            return (
              <Card
                key={wf.id}
                className="p-4 flex flex-col justify-between hover:border-slate-700 transition-all duration-200 bg-slate-900/70 group"
              >
                <div className="space-y-3">
                  {/* Top Badges */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <Badge
                        variant={isPublished ? "success" : isArchived ? "secondary" : "default"}
                        className="text-[10px] uppercase font-mono"
                      >
                        {wf.status}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] font-mono">
                        v{wf.version}
                      </Badge>
                    </div>

                    <div className="text-[11px] text-slate-400 font-mono">
                      {wf.runs_count ?? 0} runs
                    </div>
                  </div>

                  {/* Title and Description */}
                  <div>
                    <Link
                      href={`/app/workflows/${wf.id}`}
                      className="text-sm font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors flex items-center justify-between"
                    >
                      <span className="truncate">{wf.name}</span>
                      <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all text-indigo-400 shrink-0 ml-1" />
                    </Link>
                    <p className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                      {wf.description || "No description provided."}
                    </p>
                  </div>

                  {/* Steps tags */}
                  <div className="flex items-center gap-1.5 pt-1">
                    <span className="text-[11px] text-slate-400 font-mono">
                      {stepsCount} step{stepsCount !== 1 ? "s" : ""}
                    </span>
                    <span className="text-slate-700">•</span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(wf.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="pt-4 mt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <Button
                      size="sm"
                      variant="primary"
                      className="h-8 text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-500"
                      onClick={() => setRunningWorkflow(wf)}
                      disabled={isActioning || isArchived}
                    >
                      <Play className="w-3 h-3 fill-white" />
                      <span>Run</span>
                    </Button>
                    <Link href={`/app/workflows/${wf.id}`}>
                      <Button size="sm" variant="outline" className="h-8 text-xs gap-1.5">
                        <Edit className="w-3 h-3" />
                        <span>Edit</span>
                      </Button>
                    </Link>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleDuplicate(wf)}
                      disabled={isActioning}
                      className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors"
                      title="Duplicate workflow"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(wf)}
                      disabled={isActioning}
                      className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded transition-colors"
                      title="Delete workflow"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Modals */}
      <CreateWorkflowModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={(newWf) => setWorkflows((prev) => [newWf, ...prev])}
      />

      {runningWorkflow && (
        <RunWorkflowModal
          isOpen={Boolean(runningWorkflow)}
          onClose={() => setRunningWorkflow(null)}
          workflow={runningWorkflow}
        />
      )}
    </div>
  );
}

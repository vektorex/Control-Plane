"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StatCard } from "@/components/ui/StatCard";
import { QuickActionCards } from "@/components/features/dashboard/QuickActionCards";
import { ActiveWorkflows } from "@/components/features/dashboard/ActiveWorkflows";
import { CreateTaskModal } from "@/components/features/tasks/CreateTaskModal";
import { CreateProjectModal } from "@/components/features/projects/CreateProjectModal";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { PlusCircle, Sparkles, Layers, FolderKanban, ListTodo, Zap, ArrowUpRight, RefreshCw } from "lucide-react";
import { siteConfig } from "@/config/site";
import { useWorkspace } from "@/lib/workspaceContext";
import { workspaceService } from "@/services/workspaces";
import { taskService } from "@/services/tasks";
import { formatDate } from "@/lib/utils";

export default function DashboardPage() {
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const { activeWorkspace, fetchWorkspaces } = useWorkspace();

  const loadDashboardData = async () => {
    if (!activeWorkspace?.id) return;
    try {
      setIsLoading(true);
      const [projRes, tasksRes] = await Promise.all([
        workspaceService.listWorkspaceProjects(activeWorkspace.id).catch(() => ({ projects: [] })),
        taskService.listTasks().catch(() => ({ tasks: [] })),
      ]);
      setProjects(projRes?.projects || []);
      setTasks(tasksRes?.tasks || []);
    } catch (err) {
      console.error("[Dashboard] Error loading data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [activeWorkspace?.id]);

  const activeTasksCount = tasks.filter((t) => t.status === "active").length;
  const completedTasksCount = tasks.filter((t) => t.status === "completed").length;

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-850">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              {siteConfig.name}
            </h1>
            <Badge variant="primary" dot className="text-[11px]">
              PostgreSQL Layer Connected
            </Badge>
          </div>
          <p className="text-xs text-slate-400">
            Workspace: <strong className="text-slate-200">{activeWorkspace?.name || "Loading..."}</strong>
            {activeWorkspace?.slug && <span className="text-indigo-400 font-mono"> (/{activeWorkspace.slug})</span>}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={loadDashboardData}>
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={Sparkles}
            onClick={() => setIsTaskModalOpen(true)}
            disabled={!activeWorkspace?.id}
          >
            Dispatch Task
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Projects"
          value={projects.length.toString()}
          change={`${projects.length} configured`}
          changeType="positive"
          icon={FolderKanban}
          description="in workspace"
        />
        <StatCard
          title="Total Work Tasks"
          value={tasks.length.toString()}
          change={`${activeTasksCount} active`}
          changeType="positive"
          icon={ListTodo}
          description="tracked in database"
        />
        <StatCard
          title="Completed Tasks"
          value={completedTasksCount.toString()}
          change={`${tasks.length > 0 ? Math.round((completedTasksCount / tasks.length) * 100) : 0}%`}
          changeType="positive"
          icon={Zap}
          description="completion rate"
        />
        <StatCard
          title="Active Workspace"
          value={activeWorkspace?.name ? "Ready" : "—"}
          change={activeWorkspace?.slug || "default"}
          changeType="positive"
          icon={Layers}
          description="PostgreSQL persistence"
        />
      </div>

      {/* Quick Action Cards */}
      <QuickActionCards
        onOpenCreateTask={() => setIsTaskModalOpen(true)}
        onOpenCreateProject={() => setIsProjectModalOpen(true)}
      />

      {/* Pipeline Architecture Diagram */}
      <ActiveWorkflows />

      {/* Recent Dispatches Feed */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Orchestrated Tasks</CardTitle>
              <CardDescription>Live feed of task persistence states across your workspace</CardDescription>
            </div>
            <Link
              href="/app/tasks"
              className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              <span>View all tasks</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {tasks.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">
              No tasks found. Click "Dispatch Task" to create your first task.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {tasks.slice(0, 5).map((t) => (
                <div
                  key={t.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-850/50 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-indigo-400">{t.id.slice(0, 8)}...</span>
                      <span className="text-xs text-slate-200 font-medium">{t.title}</span>
                    </div>
                    {t.description && (
                      <div className="text-[11px] text-slate-400 line-clamp-1">
                        {t.description}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-4 shrink-0 sm:justify-end">
                    <Badge variant={t.status === "completed" ? "success" : t.status === "active" ? "info" : "warning"} dot>
                      {t.status}
                    </Badge>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {formatDate(t.created_at || t.createdAt)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      <CreateTaskModal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        projects={projects}
        onTaskCreated={(newTask) => setTasks((prev) => [newTask, ...prev])}
      />

      <CreateProjectModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        workspaceId={activeWorkspace?.id}
        onProjectCreated={(newProj) => setProjects((prev) => [newProj, ...prev])}
      />
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { ExecutionMetrics } from "@/components/features/dashboard/ExecutionMetrics";
import { ActiveWorkflows } from "@/components/features/dashboard/ActiveWorkflows";
import { QuickActionCards } from "@/components/features/dashboard/QuickActionCards";
import { RecentActivity } from "@/components/features/dashboard/RecentActivity";
import { CreateTaskModal } from "@/components/features/tasks/CreateTaskModal";
import { CreateProjectModal } from "@/components/features/projects/CreateProjectModal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { PlusCircle, Sparkles } from "lucide-react";
import { siteConfig } from "@/config/site";

export default function DashboardPage() {
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  const initialProjects = [
    { id: "proj-1", name: "Default Workspace", taskCount: 8, contextSourcesCount: 3 },
    { id: "proj-2", name: "Autonomous Research Lab", taskCount: 14, contextSourcesCount: 6 },
    { id: "proj-3", name: "Data Engineering Pipeline", taskCount: 5, contextSourcesCount: 2 },
  ];

  const handleTaskSubmit = (newTask) => {
    // In a real application, this dispatches to the FastAPI backend service
    console.log("[Orchestrator] Task queued for dispatch:", newTask);
  };

  const handleProjectSubmit = (newProject) => {
    console.log("[Orchestrator] Project workspace created:", newProject);
  };

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
              Orchestrator Ready
            </Badge>
          </div>
          <p className="text-xs text-slate-400">
            {siteConfig.tagline}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            icon={Sparkles}
            onClick={() => setIsTaskModalOpen(true)}
          >
            Dispatch Task
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <ExecutionMetrics />

      {/* Quick Action Cards */}
      <QuickActionCards
        onOpenCreateTask={() => setIsTaskModalOpen(true)}
        onOpenCreateProject={() => setIsProjectModalOpen(true)}
      />

      {/* Pipeline Architecture Diagram */}
      <ActiveWorkflows />

      {/* Recent Dispatches Feed */}
      <RecentActivity />

      {/* Modals */}
      <CreateTaskModal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        onSubmitTask={handleTaskSubmit}
        projects={initialProjects}
      />

      <CreateProjectModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        onSubmitProject={handleProjectSubmit}
      />
    </div>
  );
}

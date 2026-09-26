"use client";

import React, { useState } from "react";
import { ProjectGrid } from "@/components/features/projects/ProjectGrid";
import { CreateProjectModal } from "@/components/features/projects/CreateProjectModal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Plus, FolderKanban } from "lucide-react";

export default function ProjectsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [projects, setProjects] = useState([
    {
      id: "proj-1",
      name: "Default Workspace",
      description: "General orchestration pool for unassigned LLM tasks, exploratory prompts, and sandbox experiments.",
      taskCount: 8,
      contextSourcesCount: 3,
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    },
    {
      id: "proj-2",
      name: "Autonomous Research Lab",
      description: "Long-horizon synthesis of research papers, telemetry transcripts, and architecture decision logs.",
      taskCount: 14,
      contextSourcesCount: 6,
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    },
    {
      id: "proj-3",
      name: "Data Engineering Pipeline",
      description: "Automated SQL schema migrations, DBT model generation, and data quality check validation scripts.",
      taskCount: 5,
      contextSourcesCount: 2,
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1).toISOString(),
    },
  ]);

  const handleCreateProject = (newProject) => {
    setProjects([newProject, ...projects]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-850">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Project Scopes
            </h1>
            <Badge variant="primary" className="text-[11px] font-mono">
              {projects.length} Active
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Isolate domain contexts, assign custom toolkits, and partition orchestration histories.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={Plus}
          onClick={() => setIsCreateModalOpen(true)}
        >
          New Project
        </Button>
      </div>

      {/* Projects Grid */}
      <ProjectGrid
        projects={projects}
        onOpenCreateProject={() => setIsCreateModalOpen(true)}
      />

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmitProject={handleCreateProject}
      />
    </div>
  );
}

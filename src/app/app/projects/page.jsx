"use client";

import React, { useState, useEffect } from "react";
import { ProjectGrid } from "@/components/features/projects/ProjectGrid";
import { CreateProjectModal } from "@/components/features/projects/CreateProjectModal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Plus, FolderKanban, RefreshCw, Layers, ListTodo, Calendar, Trash2 } from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { workspaceService } from "@/services/workspaces";
import { projectService } from "@/services/projects";
import { formatDate } from "@/lib/utils";

export default function ProjectsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const { activeWorkspace } = useWorkspace();

  const fetchProjects = async () => {
    if (!activeWorkspace?.id) return;
    try {
      setIsLoading(true);
      setError(null);
      const res = await workspaceService.listWorkspaceProjects(activeWorkspace.id);
      setProjects(res?.projects || []);
    } catch (err) {
      console.error("[ProjectsPage] Error loading projects:", err);
      setError(err.message || "Failed to load projects for current workspace");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeWorkspace?.id]);

  const handleProjectCreated = (newProject) => {
    setProjects((prev) => [newProject, ...prev]);
  };

  const handleDeleteProject = async (projectId) => {
    if (!confirm("Are you sure you want to delete this project? All associated tasks and runs will be deleted.")) {
      return;
    }
    try {
      setIsDeleting(true);
      await projectService.deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
      setSelectedProject(null);
    } catch (err) {
      alert(`Failed to delete project: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
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
            Workspace: <strong className="text-slate-200">{activeWorkspace?.name || "Loading..."}</strong>
            {activeWorkspace?.slug && <span className="text-indigo-400 font-mono"> (/{activeWorkspace.slug})</span>}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchProjects}>
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={() => setIsCreateModalOpen(true)}
            disabled={!activeWorkspace?.id}
          >
            New Project
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchProjects}>
            Retry
          </Button>
        </div>
      )}

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-xl bg-slate-900/60 border border-slate-800/60 animate-pulse" />
          ))}
        </div>
      ) : (
        <ProjectGrid
          projects={projects}
          onOpenCreateProject={() => setIsCreateModalOpen(true)}
          onSelectProject={(proj) => setSelectedProject(proj)}
        />
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        workspaceId={activeWorkspace?.id}
        onProjectCreated={handleProjectCreated}
      />

      {/* Project Detail Modal */}
      {selectedProject && (
        <Modal
          isOpen={!!selectedProject}
          onClose={() => setSelectedProject(null)}
          title={selectedProject.name}
          description={`Project Scope (${selectedProject.slug}) in workspace ${activeWorkspace?.name || ""}`}
          footer={
            <div className="flex items-center justify-between w-full">
              <Button
                variant="destructive"
                size="sm"
                icon={Trash2}
                onClick={() => handleDeleteProject(selectedProject.id)}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete Project"}
              </Button>
              <Button variant="outline" size="sm" onClick={() => setSelectedProject(null)}>
                Close
              </Button>
            </div>
          }
        >
          <div className="space-y-4 text-xs">
            <div>
              <span className="text-slate-400 block font-medium mb-1">Description</span>
              <p className="text-slate-200 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed">
                {selectedProject.description || "No description provided."}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 font-mono">Tasks Count</span>
                <div className="text-sm font-bold text-white">
                  {selectedProject.task_count ?? selectedProject.taskCount ?? 0}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-400 font-mono">Created Date</span>
                <div className="text-sm font-bold text-slate-200">
                  {formatDate(selectedProject.created_at || selectedProject.createdAt)}
                </div>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-800/40 text-[11px] text-indigo-300 font-mono">
              ID: {selectedProject.id}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

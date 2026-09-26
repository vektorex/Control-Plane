import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/utils";
import { FolderKanban, Layers, ListTodo, Database, ArrowRight, Plus } from "lucide-react";

export function ProjectGrid({ projects = [], onOpenCreateProject, onSelectProject }) {
  if (projects.length === 0) {
    return (
      <EmptyState
        icon={FolderKanban}
        title="No project workspaces found"
        description="Create a project to group related LLM tasks, context sources, and knowledge repositories."
        actionLabel="Create Project"
        onAction={onOpenCreateProject}
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <Card
          key={project.id}
          hoverable
          className="flex flex-col justify-between cursor-pointer group"
          onClick={() => onSelectProject?.(project)}
        >
          <CardHeader>
            <div className="flex items-start justify-between gap-2">
              <div className="p-2.5 rounded-lg bg-indigo-950/50 border border-indigo-800/40 text-indigo-400">
                <FolderKanban className="w-5 h-5" />
              </div>
              <Badge variant="outline" className="text-[10px] font-mono">
                {project.id}
              </Badge>
            </div>
            <CardTitle className="mt-3 group-hover:text-indigo-300 transition-colors">
              {project.name}
            </CardTitle>
            <CardDescription className="line-clamp-2 mt-1">
              {project.description || "No description provided."}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 py-3">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/60 flex items-center gap-2">
                <ListTodo className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-300 font-medium">{project.taskCount || 0} Tasks</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/60 flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-300 font-medium">{project.contextSourcesCount || 0} Contexts</span>
              </div>
            </div>
          </CardContent>

          <CardFooter className="pt-3 flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/60">
            <span>Created {formatDate(project.createdAt)}</span>
            <div className="flex items-center gap-1 text-indigo-400 group-hover:translate-x-0.5 transition-transform font-medium">
              <span>Enter Project</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}

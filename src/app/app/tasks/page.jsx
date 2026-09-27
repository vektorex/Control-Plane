"use client";

import React, { useState, useEffect, useMemo } from "react";
import { TaskFilterBar } from "@/components/features/tasks/TaskFilterBar";
import { TaskList } from "@/components/features/tasks/TaskList";
import { CreateTaskModal } from "@/components/features/tasks/CreateTaskModal";
import { TaskDetailDrawer } from "@/components/features/tasks/TaskDetailDrawer";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { PlusCircle, RefreshCw } from "lucide-react";
import { useWorkspace } from "@/lib/workspaceContext";
import { taskService } from "@/services/tasks";
import { workspaceService } from "@/services/workspaces";

export default function TasksPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedTask, setSelectedTask] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const { activeWorkspace } = useWorkspace();

  const fetchTasksAndProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Load tasks
      const params = statusFilter !== "ALL" ? { status: statusFilter } : {};
      const tasksRes = await taskService.listTasks(params);
      setTasks(tasksRes?.tasks || []);

      // Load projects for modal
      if (activeWorkspace?.id) {
        const projRes = await workspaceService.listWorkspaceProjects(activeWorkspace.id);
        setProjects(projRes?.projects || []);
      }
    } catch (err) {
      console.error("[TasksPage] Error loading tasks:", err);
      setError(err.message || "Failed to load tasks from backend");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasksAndProjects();
  }, [activeWorkspace?.id, statusFilter]);

  const handleTaskCreated = (newTask) => {
    setTasks((prev) => [newTask, ...prev]);
  };

  const handleTaskUpdated = (updatedTask) => {
    setTasks((prev) => prev.map((t) => (t.id === updatedTask.id ? updatedTask : t)));
    setSelectedTask(updatedTask);
  };

  const handleTaskDeleted = (taskId) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    setSelectedTask(null);
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        task.title?.toLowerCase().includes(q) ||
        task.description?.toLowerCase().includes(q) ||
        task.id?.toLowerCase().includes(q)
      );
    });
  }, [tasks, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-850">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Work Tasks
            </h1>
            <Badge variant="primary" className="text-[11px] font-mono">
              {tasks.length} Total
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track goals, manage lifecycle states, and inspect historical execution runs from PostgreSQL.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchTasksAndProjects}>
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={PlusCircle}
            onClick={() => setIsCreateModalOpen(true)}
          >
            New Task
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchTasksAndProjects}>
            Retry
          </Button>
        </div>
      )}

      {/* Filter Toolbar */}
      <TaskFilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
      />

      {/* Task List Table */}
      {isLoading ? (
        <div className="p-8 text-center text-xs text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
          Loading tasks from database...
        </div>
      ) : (
        <TaskList
          tasks={filteredTasks}
          onSelectTask={(task) => setSelectedTask(task)}
          onOpenCreateTask={() => setIsCreateModalOpen(true)}
        />
      )}

      {/* Task Detail Drawer */}
      <TaskDetailDrawer
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
        onTaskUpdated={handleTaskUpdated}
        onTaskDeleted={handleTaskDeleted}
      />

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        projects={projects}
        onTaskCreated={handleTaskCreated}
      />
    </div>
  );
}

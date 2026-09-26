"use client";

import React, { useState, useMemo } from "react";
import { TaskFilterBar } from "@/components/features/tasks/TaskFilterBar";
import { TaskList } from "@/components/features/tasks/TaskList";
import { CreateTaskModal } from "@/components/features/tasks/CreateTaskModal";
import { TaskDetailDrawer } from "@/components/features/tasks/TaskDetailDrawer";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { PlusCircle, ListTodo } from "lucide-react";

export default function TasksPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [selectedTask, setSelectedTask] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const [projects] = useState([
    { id: "proj-1", name: "Default Workspace" },
    { id: "proj-2", name: "Autonomous Research Lab" },
    { id: "proj-3", name: "Data Engineering Pipeline" },
  ]);

  const [tasks, setTasks] = useState([
    {
      id: "task-101",
      title: "Synthesize quarterly risk metrics from engineering transcripts",
      prompt: "Extract risk factors, key deadlines, dependencies, and architectural debt from weekly design reviews over Q3. Group by severity and team.",
      projectId: "proj-2",
      projectName: "Autonomous Research Lab",
      modelAssigned: "Claude 3.5 Sonnet",
      priority: "high",
      status: "COMPLETED",
      retrievalStrategy: "Hybrid RAG",
      createdAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    },
    {
      id: "task-102",
      title: "Generate multi-tenant database migration and rollback script",
      prompt: "Construct a PostgreSQL zero-downtime migration for tenant isolation, adding tenant_id foreign keys and RLS policies.",
      projectId: "proj-3",
      projectName: "Data Engineering Pipeline",
      modelAssigned: "GPT-4o",
      priority: "critical",
      status: "PROCESSING",
      retrievalStrategy: "Direct Context Window",
      createdAt: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    },
    {
      id: "task-103",
      title: "Perform security audit across OpenAPI route handlers",
      prompt: "Scan route definitions, validate parameter schemas, and check for missing auth scopes or unvalidated redirect vectors.",
      projectId: "proj-1",
      projectName: "Default Workspace",
      modelAssigned: "Auto Routing",
      priority: "medium",
      status: "ROUTING",
      retrievalStrategy: "Knowledge Graph Hierarchy",
      createdAt: new Date(Date.now() - 1000 * 60 * 300).toISOString(),
    },
    {
      id: "task-104",
      title: "Extract customer sentiment signals from telemetry dumps",
      prompt: "Aggregate crash dumps and user feedback tickets to generate actionable product defect priorities.",
      projectId: "proj-2",
      projectName: "Autonomous Research Lab",
      modelAssigned: "Gemini 1.5 Pro",
      priority: "low",
      status: "COMPLETED",
      retrievalStrategy: "Hybrid RAG",
      createdAt: new Date(Date.now() - 1000 * 60 * 720).toISOString(),
    },
  ]);

  const handleCreateTask = (newTask) => {
    setTasks([newTask, ...tasks]);
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const matchesSearch =
        searchQuery === "" ||
        task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
        task.id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === "ALL" || task.status === statusFilter;
      const matchesPriority = priorityFilter === "ALL" || task.priority === priorityFilter;

      return matchesSearch && matchesStatus && matchesPriority;
    });
  }, [tasks, searchQuery, statusFilter, priorityFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-850">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Orchestrated Work Tasks
            </h1>
            <Badge variant="primary" className="text-[11px] font-mono">
              {tasks.length} total
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage incoming tasks, inspect dynamic model selection, and monitor execution state.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={PlusCircle}
          onClick={() => setIsCreateModalOpen(true)}
        >
          Dispatch Task
        </Button>
      </div>

      {/* Filter Toolbar */}
      <TaskFilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        priorityFilter={priorityFilter}
        onPriorityFilterChange={setPriorityFilter}
      />

      {/* Task List Table */}
      <TaskList
        tasks={filteredTasks}
        onSelectTask={(task) => setSelectedTask(task)}
        onOpenCreateTask={() => setIsCreateModalOpen(true)}
      />

      {/* Task Detail Drawer */}
      <TaskDetailDrawer
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
      />

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmitTask={handleCreateTask}
        projects={projects}
      />
    </div>
  );
}

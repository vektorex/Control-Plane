import React from "react";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/utils";
import { ListTodo, ArrowRight, Clock, Cpu, Layers } from "lucide-react";

export function TaskList({ tasks = [], onSelectTask, onOpenCreateTask }) {
  if (tasks.length === 0) {
    return (
      <EmptyState
        icon={ListTodo}
        title="No orchestrated tasks found"
        description="Submit a prompt or work specification to let the orchestrator route models and tools."
        actionLabel="Dispatch First Task"
        onAction={onOpenCreateTask}
      />
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case "COMPLETED":
        return <Badge variant="success" dot>Completed</Badge>;
      case "PROCESSING":
        return <Badge variant="info" dot>Processing</Badge>;
      case "ROUTING":
        return <Badge variant="primary" dot>Routing</Badge>;
      case "PENDING":
        return <Badge variant="warning" dot>Pending</Badge>;
      case "FAILED":
        return <Badge variant="destructive" dot>Failed</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case "critical":
        return <Badge variant="destructive">Critical</Badge>;
      case "high":
        return <Badge variant="warning">High</Badge>;
      case "medium":
        return <Badge variant="default">Medium</Badge>;
      case "low":
        return <Badge variant="outline">Low</Badge>;
      default:
        return <Badge variant="outline">{priority}</Badge>;
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[120px]">Task ID</TableHead>
            <TableHead>Task Goal & Description</TableHead>
            <TableHead className="w-[160px]">Project Scope</TableHead>
            <TableHead className="w-[140px]">Target Model</TableHead>
            <TableHead className="w-[110px]">Priority</TableHead>
            <TableHead className="w-[120px]">Status</TableHead>
            <TableHead className="w-[140px]">Created</TableHead>
            <TableHead className="w-[40px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow
              key={task.id}
              onClick={() => onSelectTask(task)}
              className="cursor-pointer group"
            >
              <TableCell className="font-mono text-xs text-indigo-400 font-medium">
                {task.id}
              </TableCell>
              <TableCell>
                <div className="font-medium text-slate-200 group-hover:text-indigo-300 transition-colors">
                  {task.title}
                </div>
                <div className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                  {task.prompt}
                </div>
              </TableCell>
              <TableCell className="text-xs text-slate-300">
                <span className="inline-flex items-center gap-1">
                  <Layers className="w-3 h-3 text-slate-400" />
                  {task.projectName || "Default Workspace"}
                </span>
              </TableCell>
              <TableCell>
                <span className="inline-flex items-center gap-1.5 text-xs text-slate-300 font-mono">
                  <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                  {task.modelAssigned || "Auto Routing"}
                </span>
              </TableCell>
              <TableCell>{getPriorityBadge(task.priority)}</TableCell>
              <TableCell>{getStatusBadge(task.status)}</TableCell>
              <TableCell className="text-xs text-slate-400 font-mono">
                {formatDate(task.createdAt)}
              </TableCell>
              <TableCell className="text-right">
                <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

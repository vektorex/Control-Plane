import React from "react";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/utils";
import { ListTodo, ArrowRight, Zap } from "lucide-react";

export function TaskList({ tasks = [], onSelectTask, onOpenCreateTask }) {
  if (tasks.length === 0) {
    return (
      <EmptyState
        icon={ListTodo}
        title="No tasks found"
        description="Create a task to track your work goals and inspect execution runs."
        actionLabel="Create First Task"
        onAction={onOpenCreateTask}
      />
    );
  }

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return <Badge variant="success" dot>Completed</Badge>;
      case "active":
        return <Badge variant="info" dot>Active</Badge>;
      case "draft":
        return <Badge variant="warning" dot>Draft</Badge>;
      case "archived":
        return <Badge variant="outline">Archived</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[120px]">Task ID</TableHead>
            <TableHead>Task Goal & Description</TableHead>
            <TableHead className="w-[120px]">Status</TableHead>
            <TableHead className="w-[100px]">Runs</TableHead>
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
                {task.id ? `${task.id.slice(0, 8)}...` : "—"}
              </TableCell>
              <TableCell>
                <div className="font-medium text-slate-200 group-hover:text-indigo-300 transition-colors">
                  {task.title}
                </div>
                {task.description && (
                  <div className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                    {task.description}
                  </div>
                )}
              </TableCell>
              <TableCell>{getStatusBadge(task.status)}</TableCell>
              <TableCell className="text-xs text-slate-300">
                <span className="inline-flex items-center gap-1 font-mono">
                  <Zap className="w-3 h-3 text-amber-400" />
                  {task.run_count ?? 0}
                </span>
              </TableCell>
              <TableCell className="text-xs text-slate-400 font-mono">
                {formatDate(task.created_at || task.createdAt || new Date())}
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

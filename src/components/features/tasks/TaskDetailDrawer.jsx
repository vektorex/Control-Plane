"use client";

import React, { useState, useEffect } from "react";
import { X, Cpu, Clock, CheckCircle2, AlertCircle, Zap, Trash2, Loader2, Play } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatDate } from "@/lib/utils";
import { taskService } from "@/services/tasks";

export function TaskDetailDrawer({ task, onClose, onTaskUpdated, onTaskDeleted }) {
  const [runs, setRuns] = useState([]);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (!task?.id) return;
    const fetchRuns = async () => {
      try {
        setIsLoadingRuns(true);
        const res = await taskService.listTaskRuns(task.id);
        setRuns(res?.runs || []);
      } catch (err) {
        console.error("[TaskDetailDrawer] Error loading task runs:", err);
      } finally {
        setIsLoadingRuns(false);
      }
    };
    fetchRuns();
  }, [task?.id]);

  if (!task) return null;

  const handleStatusChange = async (newStatus) => {
    try {
      setIsUpdatingStatus(true);
      const updated = await taskService.updateTask(task.id, { status: newStatus });
      onTaskUpdated?.(updated);
    } catch (err) {
      alert(`Failed to update status: ${err.message}`);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this task? All runs will be removed.")) {
      return;
    }
    try {
      setIsDeleting(true);
      await taskService.deleteTask(task.id);
      onTaskDeleted?.(task.id);
      onClose();
    } catch (err) {
      alert(`Failed to delete task: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

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

  const getRunBadge = (status) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return <Badge variant="success">Completed</Badge>;
      case "running":
        return <Badge variant="info" dot>Running</Badge>;
      case "queued":
        return <Badge variant="warning">Queued</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      case "cancelled":
        return <Badge variant="outline">Cancelled</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="relative z-50 w-full max-w-lg bg-slate-900 border-l border-slate-700 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-indigo-400 font-semibold">{task.id.slice(0, 8)}...</span>
              {getStatusBadge(task.status)}
            </div>
            <h2 className="text-base font-semibold text-slate-100 leading-snug">{task.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Status Switcher */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Lifecycle Status
            </label>
            <div className="flex items-center gap-2">
              {["draft", "active", "completed", "archived"].map((st) => (
                <button
                  key={st}
                  onClick={() => handleStatusChange(st)}
                  disabled={isUpdatingStatus || task.status === st}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors cursor-pointer ${
                    task.status === st
                      ? "bg-indigo-600 text-white font-semibold"
                      : "bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          {task.description && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Task Goal & Scope
              </h3>
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-wrap">
                {task.description}
              </div>
            </div>
          )}

          {/* Runs Execution History */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Execution Runs ({runs.length})
              </h3>
            </div>

            {isLoadingRuns ? (
              <div className="p-4 text-center text-xs text-slate-400">Loading runs...</div>
            ) : runs.length === 0 ? (
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-center text-xs text-slate-400">
                No execution runs recorded for this task yet.
              </div>
            ) : (
              <div className="space-y-2.5">
                {runs.map((run) => (
                  <div
                    key={run.id}
                    className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] text-indigo-400">{run.id.slice(0, 8)}...</span>
                        {getRunBadge(run.status)}
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {formatDate(run.created_at)}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-300 font-mono pt-1">
                      {run.model_name && (
                        <span className="flex items-center gap-1">
                          <Cpu className="w-3 h-3 text-cyan-400" />
                          {run.model_name}
                        </span>
                      )}
                      {run.total_tokens !== null && run.total_tokens !== undefined && (
                        <span className="flex items-center gap-1">
                          <Zap className="w-3 h-3 text-amber-400" />
                          {run.total_tokens} tokens
                        </span>
                      )}
                      {run.latency_ms !== null && run.latency_ms !== undefined && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-emerald-400" />
                          {run.latency_ms}ms
                        </span>
                      )}
                    </div>

                    {run.error_message && (
                      <div className="p-2 rounded bg-rose-950/40 border border-rose-900 text-rose-300 text-[11px]">
                        {run.error_message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Metadata
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-850">
                <span className="text-slate-400">Task UUID</span>
                <span className="text-slate-200 font-mono">{task.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-850">
                <span className="text-slate-400">Created At</span>
                <span className="text-slate-200 font-mono">{formatDate(task.created_at || task.createdAt)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900 flex items-center justify-between gap-2">
          <Button
            variant="destructive"
            size="sm"
            icon={Trash2}
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              icon={Play}
              onClick={() => {
                window.location.href = `/app/tasks/${task.id}`;
              }}
            >
              Open Workspace
            </Button>
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

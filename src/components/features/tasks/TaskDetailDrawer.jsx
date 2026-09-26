"use client";

import React from "react";
import { X, Cpu, Database, Wrench, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatDate } from "@/lib/utils";

export function TaskDetailDrawer({ task, onClose }) {
  if (!task) return null;

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
              <span className="font-mono text-xs text-indigo-400 font-semibold">{task.id}</span>
              <Badge variant="primary" dot>{task.status}</Badge>
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
          {/* Prompt / Specification */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Task Prompt & Goal
            </h3>
            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed font-mono whitespace-pre-wrap">
              {task.prompt}
            </div>
          </div>

          {/* Orchestrator Routing Details */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Orchestrator Routing Plan
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-850/60 border border-slate-800">
                <span className="text-slate-400 block mb-1">Assigned Model</span>
                <span className="font-medium text-slate-200 flex items-center gap-1.5 font-mono">
                  <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                  {task.modelAssigned || "Auto Routing"}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-850/60 border border-slate-800">
                <span className="text-slate-400 block mb-1">Retrieval Strategy</span>
                <span className="font-medium text-slate-200 flex items-center gap-1.5 font-mono">
                  <Database className="w-3.5 h-3.5 text-cyan-400" />
                  {task.retrievalStrategy || "Hybrid RAG"}
                </span>
              </div>
            </div>
          </div>

          {/* Metadata */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Metadata
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-850">
                <span className="text-slate-400">Project Scope</span>
                <span className="text-slate-200 font-medium">{task.projectName || "Default Workspace"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-850">
                <span className="text-slate-400">Priority Level</span>
                <span className="text-slate-200 font-medium capitalize">{task.priority}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-850">
                <span className="text-slate-400">Created At</span>
                <span className="text-slate-200 font-mono">{formatDate(task.createdAt)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900 flex items-center justify-between">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close Drawer
          </Button>
        </div>
      </div>
    </div>
  );
}

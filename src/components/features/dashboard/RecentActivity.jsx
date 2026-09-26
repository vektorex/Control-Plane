import React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";
import { ArrowUpRight, Cpu, FileCode, CheckCircle2, Clock, AlertTriangle } from "lucide-react";

export function RecentActivity() {
  const activities = [
    {
      id: "task-101",
      title: "Synthesize quarterly risk metrics from engineering transcripts",
      project: "Autonomous Research Lab",
      status: "COMPLETED",
      model: "Claude 3.5 Sonnet",
      time: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
      tokens: "18.4k tokens",
    },
    {
      id: "task-102",
      title: "Generate multi-tenant database migration and rollback script",
      project: "Data Engineering Pipeline",
      status: "PROCESSING",
      model: "GPT-4o",
      time: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      tokens: "6.2k tokens",
    },
    {
      id: "task-103",
      title: "Perform security audit across OpenAPI route handlers",
      project: "Default Workspace",
      status: "ROUTING",
      model: "Auto-Routing",
      time: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
      tokens: "Pending routing",
    },
    {
      id: "task-104",
      title: "Extract customer sentiment signals from telemetry dumps",
      project: "Autonomous Research Lab",
      status: "COMPLETED",
      model: "Gemini 1.5 Pro",
      time: new Date(Date.now() - 1000 * 60 * 360).toISOString(),
      tokens: "42.1k tokens",
    },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case "COMPLETED":
        return <Badge variant="success" dot>Completed</Badge>;
      case "PROCESSING":
        return <Badge variant="info" dot>Processing</Badge>;
      case "ROUTING":
        return <Badge variant="primary" dot>Routing</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Orchestrated Dispatches</CardTitle>
            <CardDescription>Live feed of task execution states across your workspace</CardDescription>
          </div>
          <Link
            href="/app/tasks"
            className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
          >
            <span>View all tasks</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-slate-800/80">
          {activities.map((act) => (
            <div
              key={act.id}
              className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-850/50 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{act.id}</span>
                  <span className="text-xs text-slate-300 font-medium">{act.title}</span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-slate-400">
                  <span>{act.project}</span>
                  <span>•</span>
                  <span className="font-mono text-slate-400">{act.model}</span>
                  <span>•</span>
                  <span>{act.tokens}</span>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0 sm:justify-end">
                {getStatusBadge(act.status)}
                <span className="text-[11px] text-slate-400 font-mono">{formatDate(act.time)}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

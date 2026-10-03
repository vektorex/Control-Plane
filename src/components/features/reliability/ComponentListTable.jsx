"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Filter,
  Clock,
} from "lucide-react";

export function ComponentListTable({ components = [], onRefresh }) {
  const [filterType, setFilterType] = useState("all");
  const [filterHealth, setFilterHealth] = useState("all");

  const filtered = components.filter((c) => {
    if (filterType !== "all" && c.component_type !== filterType) return false;
    if (filterHealth !== "all" && c.health_status !== filterHealth) return false;
    return true;
  });

  const getHealthBadge = (health) => {
    switch (health) {
      case "healthy":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3 h-3" /> Healthy
          </span>
        );
      case "warning":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
            <AlertTriangle className="w-3 h-3" /> Warning
          </span>
        );
      case "critical":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-red-950 text-red-400 border border-red-800">
            <XCircle className="w-3 h-3" /> Critical
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-400">
            <HelpCircle className="w-3 h-3" /> Unknown
          </span>
        );
    }
  };

  const getStatusBadge = (st) => {
    switch (st) {
      case "active":
        return <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">Active</span>;
      case "degraded":
        return <span className="text-xs px-2 py-0.5 rounded bg-amber-900/40 text-amber-300 border border-amber-800/60 font-medium">Degraded</span>;
      case "unavailable":
        return <span className="text-xs px-2 py-0.5 rounded bg-red-900/40 text-red-300 border border-red-800/60 font-medium">Unavailable</span>;
      case "maintenance":
        return <span className="text-xs px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 font-medium">Maintenance</span>;
      default:
        return <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">{st}</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">Filter By:</span>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Component Types</option>
            <option value="api">API</option>
            <option value="worker">Worker</option>
            <option value="database">Database</option>
            <option value="ai_gateway">AI Gateway</option>
            <option value="model_provider">Model Provider</option>
            <option value="workflow">Workflow</option>
            <option value="trigger">Trigger</option>
            <option value="connector">Connector</option>
            <option value="tool">Tool</option>
            <option value="cache">Semantic Cache</option>
            <option value="memory">Memory</option>
            <option value="knowledge_graph">Knowledge Graph</option>
            <option value="evaluation">Evaluation Lab</option>
          </select>

          <select
            value={filterHealth}
            onChange={(e) => setFilterHealth(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Health States</option>
            <option value="healthy">Healthy</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Showing {filtered.length} of {components.length} components
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Component</th>
              <th className="py-3 px-4 font-semibold">Type</th>
              <th className="py-3 px-4 font-semibold">Health</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Success / Fail</th>
              <th className="py-3 px-4 font-semibold">Last Heartbeat</th>
              <th className="py-3 px-4 font-semibold text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
                  No reliability components match the filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((comp) => (
                <tr key={comp.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{comp.component_name}</div>
                    <div className="text-[11px] font-mono text-slate-500">v{comp.version || "1.0.0"}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-mono text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {comp.component_type}
                    </span>
                  </td>
                  <td className="py-3 px-4">{getHealthBadge(comp.health_status)}</td>
                  <td className="py-3 px-4">{getStatusBadge(comp.status)}</td>
                  <td className="py-3 px-4 text-xs font-mono">
                    <span className="text-emerald-400">{comp.success_count}</span>
                    <span className="text-slate-600"> / </span>
                    <span className={comp.failure_count > 0 ? "text-red-400 font-bold" : "text-slate-500"}>
                      {comp.failure_count}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{comp.last_heartbeat_at ? new Date(comp.last_heartbeat_at).toLocaleTimeString() : "-"}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      href={`/app/reliability/components/${comp.id}`}
                      className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Inspect <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

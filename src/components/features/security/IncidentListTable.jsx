"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowRight,
  Clock,
  User,
  Filter,
  AlertCircle,
  CheckCircle,
  HelpCircle,
} from "lucide-react";

export function IncidentListTable({ incidents = [], onRefresh }) {
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");

  const filtered = incidents.filter((inc) => {
    if (filterSeverity !== "all" && inc.severity !== filterSeverity) return false;
    if (filterStatus !== "all" && inc.status !== filterStatus) return false;
    if (filterCategory !== "all" && inc.category !== filterCategory) return false;
    return true;
  });

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case "critical":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-950 text-red-400 border border-red-800">Critical</span>;
      case "high":
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-950 text-amber-400 border border-amber-800">High</span>;
      case "medium":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-yellow-950/80 text-yellow-400 border border-yellow-800">Medium</span>;
      case "low":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-950/80 text-blue-400 border border-blue-800">Low</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-800 text-slate-300">Info</span>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "open":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-red-900/40 text-red-300 border border-red-800/60">Open</span>;
      case "investigating":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-amber-900/40 text-amber-300 border border-amber-800/60">Investigating</span>;
      case "contained":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-900/40 text-blue-300 border border-blue-800/60">Contained</span>;
      case "resolved":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-emerald-900/40 text-emerald-300 border border-emerald-800/60">Resolved</span>;
      case "dismissed":
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-800 text-slate-400 border border-slate-700">Dismissed</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-800 text-slate-300">{status}</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Filters bar */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">Filters:</span>
          
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="contained">Contained</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Categories</option>
            <option value="prompt_injection">Prompt Injection</option>
            <option value="data_exposure">Data Exposure</option>
            <option value="authorization">Authorization</option>
            <option value="authentication">Authentication</option>
            <option value="tool_abuse">Tool Abuse</option>
            <option value="connector_abuse">Connector Abuse</option>
            <option value="workflow_abuse">Workflow Abuse</option>
            <option value="artifact_security">Artifact Security</option>
            <option value="tenant_isolation">Tenant Boundary</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Showing {filtered.length} of {incidents.length} incidents
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Incident</th>
              <th className="py-3 px-4 font-semibold">Category</th>
              <th className="py-3 px-4 font-semibold">Severity</th>
              <th className="py-3 px-4 font-semibold">Status</th>
              <th className="py-3 px-4 font-semibold">Assigned</th>
              <th className="py-3 px-4 font-semibold">Last Seen</th>
              <th className="py-3 px-4 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">
                  No security incidents match the current criteria.
                </td>
              </tr>
            ) : (
              filtered.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-medium text-white">{inc.title}</div>
                    <div className="text-xs text-slate-500 font-mono">
                      {inc.id.substring(0, 12)}...
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                      {inc.category}
                    </span>
                  </td>
                  <td className="py-3 px-4">{getSeverityBadge(inc.severity)}</td>
                  <td className="py-3 px-4">{getStatusBadge(inc.status)}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <User className="w-3.5 h-3.5" />
                      <span>{inc.assigned_to || "Unassigned"}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1 text-xs text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>
                        {inc.last_seen_at ? new Date(inc.last_seen_at).toLocaleTimeString() : "-"}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      href={`/app/security/incidents/${inc.id}`}
                      className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Investigate <ArrowRight className="w-3.5 h-3.5" />
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

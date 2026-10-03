"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Plus,
  Radio,
  Clock,
  ArrowRight,
  ShieldAlert,
  Search,
  CheckCircle2,
  Cpu,
  Layers,
} from "lucide-react";
import { collaborationService } from "@/services/collaboration";

export default function CollaborationDashboardPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("active");
  const [resourceTypeFilter, setResourceTypeFilter] = useState("");
  const [search, setSearch] = useState("");

  // Create Modal state
  const [showCreate, setShowCreate] = useState(false);
  const [newResourceType, setNewResourceType] = useState("task");
  const [newResourceId, setNewResourceId] = useState("");
  const [newWorkspaceId, setNewWorkspaceId] = useState("ws-default");
  const [creating, setCreating] = useState(false);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await collaborationService.listSessions({
        status: statusFilter || undefined,
        resource_type: resourceTypeFilter || undefined,
      });
      setSessions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load collaboration sessions", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [statusFilter, resourceTypeFilter]);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!newResourceId.trim() || creating) return;
    setCreating(true);
    try {
      const res = await collaborationService.createSession({
        workspace_id: newWorkspaceId,
        resource_type: newResourceType,
        resource_id: newResourceId.trim(),
      });
      setShowCreate(false);
      setNewResourceId("");
      fetchSessions();
    } catch (err) {
      alert(err.message || "Failed to create collaboration session");
    } finally {
      setCreating(false);
    }
  };

  const filteredSessions = sessions.filter((s) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.resource_id.toLowerCase().includes(q) || s.resource_type.toLowerCase().includes(q);
  });

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full animate-in fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Users className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Collaboration & Shared Workspaces</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time human + AI co-execution, live presence, threaded discussions, assignments, and shared decisions.
          </p>
        </div>

        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Collaboration Session</span>
        </button>
      </div>

      {/* Mandatory Governance & Trust Disclaimer */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/80 border border-indigo-500/20 text-slate-300 text-xs">
        <ShieldAlert className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Platform Governance Principle:</span> Collaboration provides
          shared application state and realtime coordination. It does not replace authorization, governance, human
          approval, or the underlying execution systems. PostgreSQL remains authoritative; real-time events are
          tenant-scoped.
        </div>
      </div>

      {/* Stats Summary Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-slate-400 text-xs font-medium">Active Shared Sessions</div>
            <div className="text-2xl font-bold text-white mt-1">
              {sessions.filter((s) => s.status === "active").length}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-slate-400 text-xs font-medium">Co-Execution Mode</div>
            <div className="text-sm font-semibold text-indigo-400 mt-1">Human-in-the-Loop Primary</div>
          </div>
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Cpu className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-slate-400 text-xs font-medium">Real-Time Infrastructure</div>
            <div className="text-sm font-semibold text-slate-300 mt-1">SSE + PostgreSQL Event Bus</div>
          </div>
          <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
            <Layers className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 bg-slate-900/50 border border-slate-800 rounded-xl">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search resource ID or type..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={resourceTypeFilter}
            onChange={(e) => setResourceTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none"
          >
            <option value="">All Resource Types</option>
            <option value="task">Tasks</option>
            <option value="workflow">Workflows</option>
            <option value="document">Documents</option>
            <option value="artifact">Artifacts</option>
            <option value="evaluation">Evaluations</option>
            <option value="security_incident">Security Incidents</option>
            <option value="recovery_exercise">Recovery Exercises</option>
            <option value="marketplace_package">Marketplace Packages</option>
          </select>

          <div className="flex items-center rounded-lg bg-slate-950 border border-slate-800 p-0.5 text-xs">
            {["active", "paused", "closed"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-md capitalize font-medium transition-all ${
                  statusFilter === st ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Sessions Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-xs text-slate-500 animate-pulse">
          Loading collaboration sessions...
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 px-4 border border-dashed border-slate-800 rounded-2xl bg-slate-900/20 text-center">
          <Users className="w-10 h-10 text-slate-600 mb-3" />
          <h3 className="text-sm font-semibold text-slate-300">No collaboration sessions found</h3>
          <p className="text-xs text-slate-500 max-w-sm mt-1">
            Create a shared workspace to collaborate with team members and AI on tasks, workflows, documents, or evaluations.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-4 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            Start Shared Workspace
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSessions.map((s) => (
            <Link
              key={s.id}
              href={`/app/collaboration/${s.id}`}
              className="group flex flex-col justify-between p-4 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/50 transition-all hover:shadow-lg hover:shadow-indigo-500/5"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {s.resource_type}
                  </span>
                  <span
                    className={`flex items-center gap-1 text-[10px] font-medium ${
                      s.status === "active" ? "text-emerald-400" : "text-slate-500"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        s.status === "active" ? "bg-emerald-400 animate-pulse" : "bg-slate-500"
                      }`}
                    />
                    {s.status}
                  </span>
                </div>

                <h3 className="text-sm font-semibold text-slate-200 group-hover:text-indigo-400 transition-colors truncate">
                  {s.resource_id}
                </h3>
                <p className="text-[11px] text-slate-500 font-mono mt-0.5 truncate">Session ID: {s.id}</p>
              </div>

              <div className="flex items-center justify-between pt-3 mt-4 border-t border-slate-800 text-[11px] text-slate-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(s.last_activity_at).toLocaleDateString()}
                </span>
                <span className="flex items-center gap-1 text-indigo-400 font-medium group-hover:translate-x-0.5 transition-transform">
                  Enter Session <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create Session Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <form
            onSubmit={handleCreateSession}
            className="flex flex-col gap-4 w-full max-w-md p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl"
          >
            <div>
              <h3 className="text-sm font-bold text-white">Create Shared Collaboration Workspace</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Initialize a real-time multi-user session on an underlying resource.
              </p>
            </div>

            <div className="flex flex-col gap-3 text-xs">
              <div>
                <label className="text-slate-400 font-medium mb-1 block">Resource Type</label>
                <select
                  value={newResourceType}
                  onChange={(e) => setNewResourceType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="task">Task</option>
                  <option value="run">Execution Run</option>
                  <option value="workflow">Workflow</option>
                  <option value="document">Document</option>
                  <option value="artifact">Artifact</option>
                  <option value="evaluation">Evaluation</option>
                  <option value="security_incident">Security Incident</option>
                  <option value="recovery_exercise">Recovery Exercise</option>
                  <option value="marketplace_package">Marketplace Package</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 font-medium mb-1 block">Resource Identifier</label>
                <input
                  type="text"
                  required
                  value={newResourceId}
                  onChange={(e) => setNewResourceId(e.target.value)}
                  placeholder="e.g. task-analytics-review-01 or doc-q3-plan"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 font-medium mb-1 block">Workspace Scope</label>
                <input
                  type="text"
                  value={newWorkspaceId}
                  onChange={(e) => setNewWorkspaceId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating || !newResourceId.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                {creating ? "Creating..." : "Create Session"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

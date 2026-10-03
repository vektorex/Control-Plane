"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Users,
  Shield,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Layers,
  ArrowLeft,
} from "lucide-react";
import { organizationService } from "@/services/organizations";
import { workspaceService } from "@/services/workspaces";

export default function WorkspaceMembersPage() {
  const { workspaceId } = useParams();

  const [workspace, setWorkspace] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [wsRes, memRes] = await Promise.all([
        workspaceService.getWorkspace(workspaceId),
        organizationService.listWorkspaceMembers(workspaceId),
      ]);
      setWorkspace(wsRes);
      setMembers(memRes?.members || []);
    } catch (err) {
      setError(err.message || "Failed to load workspace members");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (workspaceId) {
      loadData();
    }
  }, [workspaceId]);

  const handleRoleChange = async (memberId, newRole) => {
    try {
      await organizationService.updateWorkspaceMember(workspaceId, memberId, {
        role: newRole,
      });
      setSuccess("Workspace role updated.");
      setTimeout(() => setSuccess(null), 3000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to update role");
    }
  };

  const handleRemove = async (memberId) => {
    if (!confirm("Remove this member from the workspace?")) return;
    try {
      await organizationService.removeWorkspaceMember(workspaceId, memberId);
      setSuccess("Member removed from workspace.");
      setTimeout(() => setSuccess(null), 3000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to remove member");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app" className="hover:text-slate-200">
              Workspace
            </Link>
            <span>/</span>
            <span className="text-slate-100 font-medium">Team Members</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            {workspace?.name || "Workspace"} Members
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage granular workspace-level access (Admin, Member, Viewer). Workspace roles restrict organization permissions.
          </p>
        </div>

        <Link
          href="/app"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Workspace</span>
        </Link>
      </div>

      {success && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 overflow-hidden">
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Assigned Members ({members.length})</h3>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-2">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            <span className="text-xs">Loading members...</span>
          </div>
        ) : members.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No specific workspace members assigned. Organization owner and workspace creator have default administration.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800/80">
                <tr>
                  <th className="px-4 py-3">User ID</th>
                  <th className="px-4 py-3">Workspace Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Assigned Date</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {members.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-slate-300">
                      User {m.user_id.slice(0, 8)}...{m.user_id.slice(-4)}
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={m.role}
                        onChange={(e) => handleRoleChange(m.id, e.target.value)}
                        className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 capitalize focus:outline-none focus:border-indigo-500"
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Member</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 capitalize">
                        {m.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {new Date(m.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleRemove(m.id)}
                        className="p-1 rounded text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
                        title="Remove Member"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

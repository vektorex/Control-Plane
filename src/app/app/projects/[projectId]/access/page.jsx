"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  FolderKanban,
  Shield,
  Users,
  Lock,
  Globe,
  Trash2,
  Plus,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import { organizationService } from "@/services/organizations";
import { projectService } from "@/services/projects";

export default function ProjectAccessPage() {
  const { projectId } = useParams();

  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // New project member form
  const [newUserId, setNewUserId] = useState("");
  const [newRole, setNewRole] = useState("editor");
  const [isAdding, setIsAdding] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [projRes, memRes] = await Promise.all([
        projectService.getProject(projectId),
        organizationService.listProjectMembers(projectId),
      ]);
      setProject(projRes);
      setMembers(memRes?.members || []);
    } catch (err) {
      setError(err.message || "Failed to load project access settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      loadData();
    }
  }, [projectId]);

  const handleToggleAccessMode = async (mode) => {
    try {
      const updated = await projectService.updateProject(projectId, {
        access_mode: mode,
      });
      setProject(updated);
      setSuccess(`Project access mode set to ${mode}.`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      alert(err.message || "Failed to change access mode");
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!newUserId.trim()) return;

    try {
      setIsAdding(true);
      await organizationService.addProjectMember(projectId, {
        user_id: newUserId.trim(),
        role: newRole,
      });
      setNewUserId("");
      setSuccess("Project member added.");
      setTimeout(() => setSuccess(null), 3000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to add member");
    } finally {
      setIsAdding(false);
    }
  };

  const handleRoleChange = async (memberId, role) => {
    try {
      await organizationService.updateProjectMember(projectId, memberId, { role });
      setSuccess("Role updated.");
      setTimeout(() => setSuccess(null), 3000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to update role");
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!confirm("Remove member from this restricted project?")) return;
    try {
      await organizationService.removeProjectMember(projectId, memberId);
      setSuccess("Member removed.");
      setTimeout(() => setSuccess(null), 3000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to remove member");
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app" className="hover:text-slate-200">
              Workspace
            </Link>
            <span>/</span>
            <span className="text-slate-100 font-medium">Project Access</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-indigo-400" />
            {project?.name || "Project"} Access & Permissions
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure access mode (Workspace vs Restricted) and explicit project-level members.
          </p>
        </div>

        <Link
          href="/app"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Projects</span>
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

      {/* Access Mode Selector */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
          <Shield className="w-4 h-4 text-amber-400" />
          Access Mode
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Control whether all workspace collaborators can access this project or only explicitly granted members.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            onClick={() => handleToggleAccessMode("workspace")}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              project?.access_mode !== "restricted"
                ? "bg-indigo-600/10 border-indigo-500/40 shadow-sm"
                : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Globe className="w-5 h-5 text-indigo-400" />
              <div>
                <h3 className="text-xs font-semibold text-white">Workspace Mode (Default)</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  All authorized workspace members can access this project according to their workspace role.
                </p>
              </div>
            </div>
          </div>

          <div
            onClick={() => handleToggleAccessMode("restricted")}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              project?.access_mode === "restricted"
                ? "bg-amber-500/10 border-amber-500/40 shadow-sm"
                : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Lock className="w-5 h-5 text-amber-400" />
              <div>
                <h3 className="text-xs font-semibold text-white">Restricted Mode</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Only explicitly assigned project members (and organization/workspace admins) can access.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Explicit Project Members */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>Explicit Project Members ({members.length})</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Assign Editor or Viewer roles directly at the project level.
            </p>
          </div>
        </div>

        <form onSubmit={handleAddMember} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            required
            value={newUserId}
            onChange={(e) => setNewUserId(e.target.value)}
            placeholder="User UUID (e.g. 12345678-1234-...)"
            className="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
          />

          <select
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 capitalize"
          >
            <option value="editor">Editor</option>
            <option value="viewer">Viewer</option>
          </select>

          <button
            type="submit"
            disabled={isAdding || !newUserId.trim()}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50 shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Member</span>
          </button>
        </form>

        <div className="overflow-x-auto rounded-lg border border-slate-800/80">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800/80">
              <tr>
                <th className="px-4 py-2.5">User ID</th>
                <th className="px-4 py-2.5">Project Role</th>
                <th className="px-4 py-2.5">Assigned Date</th>
                <th className="px-4 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {members.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-slate-500 text-xs">
                    No explicit project members assigned.
                  </td>
                </tr>
              ) : (
                members.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-slate-300">
                      User {m.user_id.slice(0, 8)}...{m.user_id.slice(-4)}
                    </td>
                    <td className="px-4 py-2.5">
                      <select
                        value={m.role}
                        onChange={(e) => handleRoleChange(m.id, e.target.value)}
                        className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 capitalize focus:outline-none focus:border-indigo-500"
                      >
                        <option value="editor">Editor</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400">
                      {new Date(m.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={() => handleRemoveMember(m.id)}
                        className="p-1 rounded text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
                        title="Remove Member"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

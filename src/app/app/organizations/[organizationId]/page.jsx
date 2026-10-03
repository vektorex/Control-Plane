"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  Users,
  Layers,
  Settings,
  Plus,
  Shield,
  Clock,
  ArrowRight,
  Loader2,
  AlertTriangle,
  FolderGit2,
} from "lucide-react";
import { organizationService } from "@/services/organizations";
import { useOrganization } from "@/lib/organizationContext";

export default function OrganizationDetailPage() {
  const { organizationId } = useParams();
  const router = useRouter();
  const { activeOrganization, setActiveOrganization } = useOrganization();

  const [org, setOrg] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New workspace modal
  const [showWsModal, setShowWsModal] = useState(false);
  const [wsName, setWsName] = useState("");
  const [wsSlug, setWsSlug] = useState("");
  const [isCreatingWs, setIsCreatingWs] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [orgRes, wsRes] = await Promise.all([
        organizationService.getOrganization(organizationId),
        organizationService.listWorkspaces(organizationId),
      ]);
      setOrg(orgRes);
      setWorkspaces(wsRes?.workspaces || []);
    } catch (err) {
      setError(err.message || "Failed to load organization details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId) {
      loadData();
    }
  }, [organizationId]);

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!wsName.trim()) return;

    try {
      setIsCreatingWs(true);
      await organizationService.createWorkspace(organizationId, {
        name: wsName.trim(),
        slug: wsSlug.trim() || undefined,
      });
      setShowWsModal(false);
      setWsName("");
      setWsSlug("");
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to create workspace");
    } finally {
      setIsCreatingWs(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
        <p className="text-xs">Loading organization data...</p>
      </div>
    );
  }

  if (error || !org) {
    return (
      <div className="p-8 text-center rounded-xl bg-slate-900 border border-slate-800">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-white">Error Loading Organization</h3>
        <p className="text-xs text-slate-400 mt-1 mb-4">{error || "Organization not found"}</p>
        <Link
          href="/app/organizations"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-200 hover:text-white"
        >
          Back to Organizations
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/20 border border-slate-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">{org.name}</h1>
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full capitalize bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {org.status}
                </span>
              </div>
              <p className="text-xs font-mono text-slate-400 mt-0.5">@{org.slug}</p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Link
              href={`/app/organizations/${organizationId}/members`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
            >
              <Users className="w-3.5 h-3.5" />
              <span>Members & Invites</span>
            </Link>

            <Link
              href={`/app/organizations/${organizationId}/settings`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Settings</span>
            </Link>

            {activeOrganization?.id !== org.id && (
              <button
                onClick={() => setActiveOrganization(org)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-medium transition-colors cursor-pointer"
              >
                <span>Set as Active Org</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Workspaces Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Organization Workspaces</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Workspaces isolate projects, tasks, workflows, and connector credentials under this organization.
            </p>
          </div>

          {org.capabilities?.can_create_workspaces && (
            <button
              onClick={() => setShowWsModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Workspace</span>
            </button>
          )}
        </div>

        {workspaces.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-900/40 border border-slate-800/80 border-dashed">
            <Layers className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs text-slate-400">No workspaces yet under this organization.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workspaces.map((ws) => (
              <div
                key={ws.id}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 truncate">
                      <div className="w-7 h-7 rounded-md bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                        <Layers className="w-3.5 h-3.5" />
                      </div>
                      <h4 className="text-sm font-semibold text-white truncate">{ws.name}</h4>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500 truncate">/{ws.slug}</span>
                  </div>

                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                    {ws.description || "Production workspace for agentic workflows and execution."}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
                  <Link
                    href={`/app/workspaces/${ws.id}/members`}
                    className="text-slate-400 hover:text-slate-200 inline-flex items-center gap-1 text-[11px]"
                  >
                    <Users className="w-3 h-3" />
                    <span>Workspace Members</span>
                  </Link>

                  <Link
                    href="/app"
                    className="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1 text-[11px]"
                  >
                    <span>Open</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Workspace Modal */}
      {showWsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6">
            <h3 className="text-base font-semibold text-white">Create Workspace</h3>
            <p className="text-xs text-slate-400 mt-1">
              Add a new workspace to {org.name}. Workspaces contain projects, tasks, and credentials.
            </p>

            <form onSubmit={handleCreateWorkspace} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Workspace Name *
                </label>
                <input
                  type="text"
                  required
                  value={wsName}
                  onChange={(e) => {
                    setWsName(e.target.value);
                    if (!wsSlug) {
                      setWsSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""));
                    }
                  }}
                  placeholder="e.g. Production Team"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Slug (Identifier)
                </label>
                <input
                  type="text"
                  value={wsSlug}
                  onChange={(e) => setWsSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_-]+/g, ""))}
                  placeholder="e.g. prod-team"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowWsModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingWs || !wsName.trim()}
                  className="px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
                >
                  {isCreatingWs ? "Creating..." : "Create Workspace"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

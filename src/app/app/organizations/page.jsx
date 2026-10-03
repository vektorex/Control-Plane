"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  Plus,
  Users,
  Layers,
  ArrowRight,
  Shield,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { organizationService } from "@/services/organizations";
import { useOrganization } from "@/lib/organizationContext";

export default function OrganizationsPage() {
  const router = useRouter();
  const { organizations, activeOrganization, setActiveOrganization, fetchOrganizations, isLoading: isContextLoading } = useOrganization();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setIsCreating(true);
      setError(null);
      const created = await organizationService.createOrganization({
        name: name.trim(),
        slug: slug.trim() || undefined,
      });
      await fetchOrganizations();
      setActiveOrganization(created);
      setShowModal(false);
      setName("");
      setSlug("");
      router.push(`/app/organizations/${created.id}`);
    } catch (err) {
      setError(err.message || "Failed to create organization");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Building2 className="w-6 h-6 text-amber-400" />
            Organizations & Teams
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage multi-tenant organizations, workspace hierarchies, team memberships, and access controls.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all cursor-pointer shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Organization</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Organizations Grid */}
      {isContextLoading ? (
        <div className="py-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          <p className="text-xs">Loading organizations...</p>
        </div>
      ) : organizations.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800/80 border-dashed">
          <Building2 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">No organizations found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            You are not currently a member of any organization. Create one to begin organizing your team and workspaces.
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create First Organization</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {organizations.map((org) => {
            const isActive = activeOrganization?.id === org.id;
            return (
              <div
                key={org.id}
                className={`relative rounded-xl p-5 border transition-all flex flex-col justify-between ${
                  isActive
                    ? "bg-slate-900/90 border-amber-500/40 shadow-lg shadow-amber-950/20"
                    : "bg-slate-900/50 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/80"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
                        <Building2 className="w-5 h-5" />
                      </div>
                      <div className="truncate">
                        <h3 className="font-semibold text-sm text-white truncate">{org.name}</h3>
                        <p className="text-[11px] font-mono text-slate-400">@{org.slug}</p>
                      </div>
                    </div>

                    <span
                      className={`text-[10px] font-medium px-2 py-0.5 rounded-full capitalize ${
                        org.status === "active"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {org.status}
                    </span>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 grid grid-cols-2 gap-2 text-[11px]">
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <Shield className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Role:</span>
                      <span className="text-slate-200 font-medium capitalize">
                        {org.capabilities?.can_manage_members ? "Admin / Owner" : "Member"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-slate-400 justify-end">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(org.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between gap-2">
                  <button
                    onClick={() => setActiveOrganization(org)}
                    disabled={isActive}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-amber-500/20 text-amber-300 cursor-default"
                        : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white cursor-pointer"
                    }`}
                  >
                    {isActive ? "Active Organization" : "Switch To"}
                  </button>

                  <Link
                    href={`/app/organizations/${org.id}`}
                    className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    <span>Manage</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6">
            <h3 className="text-base font-semibold text-white">Create New Organization</h3>
            <p className="text-xs text-slate-400 mt-1">
              Organizations define top-level tenant boundaries for teams, workspaces, and resources.
            </p>

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Organization Name *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (!slug) {
                      setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""));
                    }
                  }}
                  placeholder="e.g. Wayne Enterprises"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Slug (Unique Identifier)
                </label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_-]+/g, ""))}
                  placeholder="e.g. wayne-enterprises"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !name.trim()}
                  className="px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
                >
                  {isCreating ? "Creating..." : "Create Organization"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

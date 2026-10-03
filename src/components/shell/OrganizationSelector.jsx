"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChevronDown, Check, Plus, Building2, Shield, Settings, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useOrganization } from "@/lib/organizationContext";

export function OrganizationSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  const {
    organizations,
    activeOrganization,
    setActiveOrganization,
    createOrganization,
    isLoading,
  } = useOrganization();

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setIsSubmitting(true);
      setFormError(null);
      await createOrganization({
        name: name.trim(),
        slug: slug.trim() || undefined,
      });
      setName("");
      setSlug("");
      setShowCreateModal(false);
      setIsOpen(false);
    } catch (err) {
      setFormError(err.message || "Failed to create organization");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 transition-colors text-left cursor-pointer group"
          aria-expanded={isOpen}
          aria-label="Select Organization"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
              <Building2 className="w-4 h-4" />
            </div>
            <div className="truncate">
              <div className="text-xs font-semibold text-slate-200 truncate">
                {isLoading ? "Loading..." : activeOrganization?.name || "Select Organization"}
              </div>
              <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                <span>{activeOrganization?.slug ? `@${activeOrganization.slug}` : "Organization"}</span>
                {activeOrganization?.capabilities?.can_manage_members && (
                  <span className="text-[9px] px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 font-semibold">
                    Admin
                  </span>
                )}
              </div>
            </div>
          </div>
          <ChevronDown
            className={cn(
              "w-4 h-4 text-slate-400 group-hover:text-slate-300 transition-transform duration-200 shrink-0",
              isOpen && "rotate-180"
            )}
          />
        </button>

        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute top-full left-0 right-0 mt-1 z-50 rounded-lg bg-slate-900 border border-slate-800 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-100">
              <div className="p-2 border-b border-slate-800/60 text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex justify-between items-center">
                <span>Organizations</span>
                <Link
                  href="/app/organizations"
                  onClick={() => setIsOpen(false)}
                  className="text-indigo-400 hover:text-indigo-300 text-[11px] normal-case"
                >
                  View All
                </Link>
              </div>

              <div className="max-h-56 overflow-y-auto p-1 space-y-0.5">
                {organizations.map((org) => {
                  const isSelected = activeOrganization?.id === org.id;
                  return (
                    <button
                      key={org.id}
                      type="button"
                      onClick={() => {
                        setActiveOrganization(org);
                        setIsOpen(false);
                      }}
                      className={cn(
                        "w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors text-left",
                        isSelected
                          ? "bg-amber-500/10 text-amber-300 font-medium"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      )}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{org.name}</span>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>

              <div className="p-1 border-t border-slate-800/60 space-y-0.5">
                {activeOrganization && (
                  <>
                    <Link
                      href={`/app/organizations/${activeOrganization.id}/members`}
                      onClick={() => setIsOpen(false)}
                      className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
                    >
                      <Users className="w-3.5 h-3.5 text-slate-400" />
                      <span>Manage Members & Invites</span>
                    </Link>
                    <Link
                      href={`/app/organizations/${activeOrganization.id}/settings`}
                      onClick={() => setIsOpen(false)}
                      className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
                    >
                      <Settings className="w-3.5 h-3.5 text-slate-400" />
                      <span>Organization Settings</span>
                    </Link>
                  </>
                )}

                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(true);
                    setIsOpen(false);
                  }}
                  className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs text-indigo-400 hover:bg-indigo-950/30 hover:text-indigo-300 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Organization</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Create Organization Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl bg-slate-900 border border-slate-800 shadow-2xl p-6">
            <h3 className="text-base font-semibold text-white">Create New Organization</h3>
            <p className="text-xs text-slate-400 mt-1">
              Organizations provide high-level multi-tenant boundaries for workspaces, teams, and members.
            </p>

            {formError && (
              <div className="mt-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                {formError}
              </div>
            )}

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
                  placeholder="e.g. Acme Corporation"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Slug (Identifier)
                </label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_-]+/g, ""))}
                  placeholder="e.g. acme-corp"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !name.trim()}
                  className="px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? "Creating..." : "Create Organization"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

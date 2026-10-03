"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Settings,
  Building2,
  Shield,
  CreditCard,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Trash2,
  Lock,
  ArrowRightLeft,
  Users,
} from "lucide-react";
import { organizationService } from "@/services/organizations";
import { useOrganization } from "@/lib/organizationContext";

export default function OrganizationSettingsPage() {
  const { organizationId } = useParams();
  const router = useRouter();
  const { fetchOrganizations } = useOrganization();

  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Ownership transfer state
  const [targetUserId, setTargetUserId] = useState("");
  const [transferring, setTransferring] = useState(false);
  const [transferConfirm, setTransferConfirm] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [orgRes, memRes] = await Promise.all([
        organizationService.getOrganization(organizationId),
        organizationService.listMembers(organizationId),
      ]);
      setOrg(orgRes);
      setName(orgRes.name);
      setSlug(orgRes.slug);
      setMembers(memRes?.members || []);
    } catch (err) {
      setError(err.message || "Failed to load organization settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId) {
      loadData();
    }
  }, [organizationId]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      const updated = await organizationService.updateOrganization(organizationId, {
        name: name.trim(),
        slug: slug.trim() || undefined,
      });
      setOrg(updated);
      setSuccess("Organization settings updated successfully.");
      setTimeout(() => setSuccess(null), 4000);
      await fetchOrganizations();
    } catch (err) {
      setError(err.message || "Failed to update organization");
    } finally {
      setSaving(false);
    }
  };

  const handleTransferOwnership = async (e) => {
    e.preventDefault();
    if (!targetUserId) {
      alert("Please select a target member to transfer ownership to.");
      return;
    }
    if (!confirm("Are you sure you want to transfer ownership? You will be demoted to Admin.")) {
      return;
    }

    try {
      setTransferring(true);
      setError(null);
      await organizationService.transferOwnership(organizationId, targetUserId);
      setSuccess("Ownership transferred successfully.");
      setTimeout(() => setSuccess(null), 4000);
      await loadData();
      await fetchOrganizations();
    } catch (err) {
      setError(err.message || "Failed to transfer ownership");
    } finally {
      setTransferring(false);
    }
  };

  const handleArchive = async () => {
    if (!confirm("Are you sure you want to archive this organization? Workspaces will become read-only.")) {
      return;
    }

    try {
      await organizationService.deleteOrganization(organizationId);
      await fetchOrganizations();
      router.push("/app/organizations");
    } catch (err) {
      alert(err.message || "Failed to archive organization");
    }
  };

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
        <p className="text-xs">Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-5">
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
          <Link href="/app/organizations" className="hover:text-slate-200">
            Organizations
          </Link>
          <span>/</span>
          <Link href={`/app/organizations/${organizationId}`} className="hover:text-slate-200">
            {org?.name || "Details"}
          </Link>
          <span>/</span>
          <span className="text-slate-100 font-medium">Settings</span>
        </div>
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-indigo-400" />
          Organization Settings & Governance
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure organization identifiers, tenant security boundaries, and ownership.
        </p>
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

      {/* General Settings Card */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
          <Building2 className="w-4 h-4 text-amber-400" />
          General Profile
        </h2>
        <p className="text-xs text-slate-400 mb-5">
          Update the public display name and slug used for scoped routing.
        </p>

        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Organization Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full max-w-md px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Organization Slug
            </label>
            <input
              type="text"
              required
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_-]+/g, ""))}
              className="w-full max-w-md px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all cursor-pointer disabled:opacity-50"
            >
              {saving ? "Saving Changes..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>

      {/* Infrastructure Safety Limits */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
          <Shield className="w-4 h-4 text-indigo-400" />
          Tenant Isolation & Safety Limits
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Infrastructure limits configured to safeguard multi-tenant database capacity.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Max Members</div>
            <div className="text-base font-bold text-slate-200 mt-1">50</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Max Workspaces</div>
            <div className="text-base font-bold text-slate-200 mt-1">20</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Workspace Members</div>
            <div className="text-base font-bold text-slate-200 mt-1">50</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Project Members</div>
            <div className="text-base font-bold text-slate-200 mt-1">30</div>
          </div>
        </div>
      </div>

      {/* Transfer Ownership Section */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
          <ArrowRightLeft className="w-4 h-4 text-amber-400" />
          Transfer Organization Ownership
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Safely transfer primary tenant ownership to another active member. You will automatically receive the Admin role.
        </p>

        <form onSubmit={handleTransferOwnership} className="space-y-3 max-w-md">
          <select
            value={targetUserId}
            onChange={(e) => setTargetUserId(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">Select active member...</option>
            {members
              .filter((m) => m.role !== "owner" && m.status === "active")
              .map((m) => (
                <option key={m.id} value={m.user_id}>
                  User {m.user_id.slice(0, 8)}... ({m.role})
                </option>
              ))}
          </select>

          <button
            type="submit"
            disabled={transferring || !targetUserId}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
          >
            {transferring ? "Transferring..." : "Transfer Ownership"}
          </button>
        </form>
      </div>

      {/* Billing Placeholder */}
      <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800/60 opacity-60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-300">Subscription & Billing</h2>
          </div>
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            Coming Soon
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Billing integrations and enterprise quotas are placeholder configurations reserved for future extensions.
        </p>
      </div>

      {/* Danger Zone */}
      <div className="p-6 rounded-xl bg-rose-950/10 border border-rose-500/20">
        <h2 className="text-sm font-semibold text-rose-400 flex items-center gap-2 mb-1">
          <Trash2 className="w-4 h-4" />
          Archive Organization
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Soft-deletes this organization. Workspaces and projects will remain safely preserved in the database.
        </p>

        <button
          onClick={handleArchive}
          className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-colors cursor-pointer"
        >
          Archive Organization
        </button>
      </div>
    </div>
  );
}

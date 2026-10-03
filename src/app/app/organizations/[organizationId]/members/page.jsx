"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Users,
  UserPlus,
  Shield,
  Trash2,
  Mail,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  MoreVertical,
  XCircle,
  Building2,
  Send,
} from "lucide-react";
import { organizationService } from "@/services/organizations";

export default function OrganizationMembersPage() {
  const { organizationId } = useParams();

  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Invite state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteError, setInviteError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [membersRes, invitesRes] = await Promise.all([
        organizationService.listMembers(organizationId),
        organizationService.listInvitations(organizationId),
      ]);
      setMembers(membersRes?.members || []);
      setInvitations(invitesRes?.invitations || []);
    } catch (err) {
      setError(err.message || "Failed to load members");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId) {
      loadData();
    }
  }, [organizationId]);

  const handleSendInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    try {
      setIsInviting(true);
      setInviteError(null);
      await organizationService.createInvitation(organizationId, {
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInviteEmail("");
      setActionSuccess("Invitation sent successfully.");
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      setInviteError(err.message || "Failed to send invitation");
    } finally {
      setIsInviting(false);
    }
  };

  const handleRoleChange = async (memberId, newRole) => {
    try {
      await organizationService.updateMember(organizationId, memberId, {
        role: newRole,
      });
      setActionSuccess("Role updated successfully.");
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to update role");
    }
  };

  const handleStatusChange = async (memberId, newStatus) => {
    try {
      await organizationService.updateMember(organizationId, memberId, {
        status: newStatus,
      });
      setActionSuccess(`Member status updated to ${newStatus}.`);
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to update member status");
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!confirm("Are you sure you want to remove this member from the organization?")) return;
    try {
      await organizationService.removeMember(organizationId, memberId);
      setActionSuccess("Member removed from organization.");
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to remove member");
    }
  };

  const handleRevokeInvite = async (inviteId) => {
    if (!confirm("Revoke this invitation?")) return;
    try {
      await organizationService.revokeInvitation(organizationId, inviteId);
      setActionSuccess("Invitation revoked.");
      setTimeout(() => setActionSuccess(null), 4000);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to revoke invitation");
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumbs / Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/organizations" className="hover:text-slate-200">
              Organizations
            </Link>
            <span>/</span>
            <Link href={`/app/organizations/${organizationId}`} className="hover:text-slate-200">
              Details
            </Link>
            <span>/</span>
            <span className="text-slate-100 font-medium">Members & Teams</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-400" />
            Organization Members & Access Control
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage organization-level roles (Owner, Admin, Member, Viewer) and send invitations.
          </p>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Invite Member Section */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
          <UserPlus className="w-4 h-4 text-indigo-400" />
          Invite Team Member
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Send a cryptographically signed invitation link to onboard a new collaborator.
        </p>

        {inviteError && (
          <div className="mb-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
            {inviteError}
          </div>
        )}

        <form onSubmit={handleSendInvite} className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@organization.com"
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="w-full sm:w-40 shrink-0">
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 capitalize"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isInviting || !inviteEmail.trim()}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all cursor-pointer disabled:opacity-50 shrink-0"
          >
            {isInviting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span>Send Invitation</span>
          </button>
        </form>
      </div>

      {/* Members Table */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 overflow-hidden">
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">Active Members ({members.length})</h3>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-2">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            <span className="text-xs">Loading members...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800/80">
                <tr>
                  <th className="px-4 py-3">Member ID</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Joined Date</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {members.map((m) => {
                  const isOwner = m.role === "owner";
                  return (
                    <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-slate-300">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-[10px] font-bold">
                            U
                          </div>
                          <span>{m.user_id.slice(0, 8)}...{m.user_id.slice(-4)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {isOwner ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold text-[10px] uppercase">
                            <Shield className="w-3 h-3" />
                            Owner
                          </span>
                        ) : (
                          <select
                            value={m.role}
                            onChange={(e) => handleRoleChange(m.id, e.target.value)}
                            className="px-2 py-1 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 capitalize focus:outline-none focus:border-indigo-500"
                          >
                            <option value="admin">Admin</option>
                            <option value="member">Member</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-[10px] font-medium px-2 py-0.5 rounded-full capitalize ${
                            m.status === "active"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}
                        >
                          {m.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {m.joined_at ? new Date(m.joined_at).toLocaleDateString() : "Pending"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {!isOwner && (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleStatusChange(m.id, m.status === "active" ? "suspended" : "active")}
                              className="px-2 py-0.5 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                            >
                              {m.status === "active" ? "Suspend" : "Activate"}
                            </button>
                            <button
                              onClick={() => handleRemoveMember(m.id)}
                              className="p-1 rounded text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
                              title="Remove Member"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invitations Section */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 overflow-hidden">
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Pending Invitations ({invitations.length})</h3>
          </div>
        </div>

        {invitations.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No pending invitations for this organization.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800/80">
                <tr>
                  <th className="px-4 py-3">Recipient Email</th>
                  <th className="px-4 py-3">Assigned Role</th>
                  <th className="px-4 py-3">Expires At</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {invitations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-200">{inv.email}</td>
                    <td className="px-4 py-3 uppercase text-[10px] font-semibold text-indigo-300">
                      {inv.role}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                      {new Date(inv.expires_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 capitalize">
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {inv.status === "pending" && (
                        <button
                          onClick={() => handleRevokeInvite(inv.id)}
                          className="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-[11px] font-medium transition-colors"
                        >
                          Revoke
                        </button>
                      )}
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

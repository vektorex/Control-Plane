"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { StatCard } from "@/components/ui/StatCard";
import { Modal } from "@/components/ui/Modal";
import { outcomeService } from "@/services/outcomes";
import {
  Scale,
  Plus,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  UserCheck,
  Cpu,
} from "lucide-react";

export default function DecisionsPage() {
  const router = useRouter();
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    title: "",
    description: "",
    decision_type: "human",
    status: "proposed",
  });

  const fetchDecisions = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter !== "ALL") params.status = statusFilter.toLowerCase();
      if (typeFilter !== "ALL") params.decision_type = typeFilter.toLowerCase();
      const data = await outcomeService.listDecisions(params);
      setDecisions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[DecisionsPage] Fetch error:", err);
      setError(err.message || "Failed to load decisions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDecisions();
  }, [statusFilter, typeFilter]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;

    try {
      setSubmitting(true);
      const payload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        decision_type: form.decision_type,
        status: form.status,
      };

      const res = await outcomeService.createDecision(payload);
      setIsModalOpen(false);
      setForm({ title: "", description: "", decision_type: "human", status: "proposed" });
      if (res?.id) {
        router.push(`/app/decisions/${res.id}`);
      } else {
        fetchDecisions();
      }
    } catch (err) {
      console.error("[DecisionsPage] Create error:", err);
      alert(err.message || "Failed to create decision");
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (id, e) => {
    e.stopPropagation();
    try {
      await outcomeService.approveDecision(id);
      fetchDecisions();
    } catch (err) {
      alert(err.message || "Failed to approve decision");
    }
  };

  const handleReject = async (id, e) => {
    e.stopPropagation();
    const reason = prompt("Enter reason for rejection:");
    if (!reason) return;
    try {
      await outcomeService.rejectDecision(id, reason);
      fetchDecisions();
    } catch (err) {
      alert(err.message || "Failed to reject decision");
    }
  };

  const filteredDecisions = decisions.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.title.toLowerCase().includes(q) ||
      (d.description && d.description.toLowerCase().includes(q))
    );
  });

  const approvedCount = decisions.filter((d) => d.status === "approved").length;
  const underReviewCount = decisions.filter((d) => d.status === "under_review").length;
  const proposedCount = decisions.filter((d) => d.status === "proposed").length;
  const rejectedCount = decisions.filter((d) => d.status === "rejected").length;

  const getDecisionBadge = (type) => {
    switch (type) {
      case "human":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 font-mono text-[10px]">HUMAN DECISION</Badge>;
      case "AI_assisted":
        return <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 font-mono text-[10px]">AI-ASSISTED</Badge>;
      case "agent":
        return <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 font-mono text-[10px]">AGENT DECISION</Badge>;
      case "policy":
        return <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 font-mono text-[10px]">POLICY GATE</Badge>;
      default:
        return <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700 font-mono text-[10px]">{type?.toUpperCase()}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <Scale className="h-6 w-6 text-indigo-400" />
            Work Decisions & Governance
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Governing human, policy, and AI-assisted decisions that steer objectives and outcome deliverables.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={fetchDecisions}
            variant="outline"
            size="sm"
            className="gap-2 border-zinc-800 text-zinc-300"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" />
            Propose Decision
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Decisions"
          value={decisions.length}
          description="Tracked decision points"
          icon={<Scale className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Approved"
          value={approvedCount}
          description="Formally ratified decisions"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Under Review"
          value={underReviewCount}
          description="Awaiting governance/human signoff"
          icon={<Clock className="h-5 w-5 text-amber-400" />}
        />
        <StatCard
          title="Rejected / Superseded"
          value={rejectedCount}
          description="Challenged or retired decisions"
          icon={<XCircle className="h-5 w-5 text-rose-400" />}
        />
      </div>

      {/* Search & Filters */}
      <Card className="p-4 bg-zinc-900/60 border-zinc-800">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search decisions by title or description..."
              className="pl-9 bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-200"
            >
              <option value="ALL">All Statuses</option>
              <option value="PROPOSED">Proposed</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="SUPERSEDED">Superseded</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-200"
            >
              <option value="ALL">All Decision Types</option>
              <option value="HUMAN">Human Decision</option>
              <option value="AI_ASSISTED">AI-Assisted</option>
              <option value="AGENT">Agent Decision</option>
              <option value="POLICY">Policy Gate</option>
              <option value="WORKFLOW">Workflow Rule</option>
              <option value="TEAM">Team Consensus</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Decisions List */}
      {loading ? (
        <div className="flex justify-center py-16">
          <RefreshCw className="h-8 w-8 animate-spin text-zinc-500" />
        </div>
      ) : filteredDecisions.length === 0 ? (
        <Card className="p-12 text-center bg-zinc-900/40 border-zinc-800">
          <Scale className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-zinc-300">No decisions found</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            {searchQuery || statusFilter !== "ALL"
              ? "Try adjusting your search query or filters."
              : "Record decisions with evidence provenance to understand why outcomes and workflows were directed."}
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredDecisions.map((d) => (
            <Card key={d.id} className="p-5 bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 transition space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {getDecisionBadge(d.decision_type)}
                    <Badge className={`text-[10px] uppercase font-mono ${
                      d.status === "approved"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : d.status === "rejected"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : "bg-zinc-800 text-zinc-400 border-zinc-700"
                    }`}>
                      {d.status}
                    </Badge>
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-100 hover:text-indigo-300 transition">
                    <Link href={`/app/decisions/${d.id}`}>{d.title}</Link>
                  </h3>
                  <p className="text-xs text-zinc-400 line-clamp-2">
                    {d.description || "No description provided."}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {d.status !== "approved" && (
                    <Button
                      size="xs"
                      onClick={(e) => handleApprove(d.id, e)}
                      className="bg-emerald-600/80 hover:bg-emerald-600 text-white text-xs gap-1"
                    >
                      <CheckCircle2 className="h-3 w-3" /> Approve
                    </Button>
                  )}
                  {d.status !== "rejected" && (
                    <Button
                      size="xs"
                      variant="outline"
                      onClick={(e) => handleReject(d.id, e)}
                      className="border-rose-900/50 text-rose-400 hover:bg-rose-950/20 text-xs gap-1"
                    >
                      <XCircle className="h-3 w-3" /> Reject
                    </Button>
                  )}
                  <Link href={`/app/decisions/${d.id}`}>
                    <Button size="xs" variant="ghost" className="gap-1 text-zinc-400 hover:text-zinc-200 text-xs">
                      Inspect <ArrowRight className="h-3 w-3" />
                    </Button>
                  </Link>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-zinc-500 font-mono pt-2 border-t border-zinc-800/80">
                <span>Owner: {d.decision_owner || "system"}</span>
                <span>Created: {new Date(d.created_at).toLocaleDateString()}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Propose Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Record New Decision">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Decision Title *</label>
            <Input
              value={form.title}
              onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              placeholder="e.g. Authorize deployment remediation plan"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Description & Context</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              rows={3}
              placeholder="Explain the background, evidence reviewed, and intended goal..."
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Decision Type *</label>
              <select
                value={form.decision_type}
                onChange={(e) => setForm((p) => ({ ...p, decision_type: e.target.value }))}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
              >
                <option value="human">Human Decision</option>
                <option value="AI_assisted">AI-Assisted</option>
                <option value="agent">Agent Decision</option>
                <option value="policy">Policy Gate</option>
                <option value="workflow">Workflow Rule</option>
                <option value="team">Team Consensus</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
              >
                <option value="proposed">Proposed</option>
                <option value="under_review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={submitting}
              className="bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              {submitting ? "Saving..." : "Record Decision"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

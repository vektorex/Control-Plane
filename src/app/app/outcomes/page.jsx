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
  Award,
  Plus,
  Search,
  RefreshCw,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Target,
  FileCheck,
  Sparkles,
} from "lucide-react";

export default function OutcomesPage() {
  const router = useRouter();
  const [outcomes, setOutcomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    name: "",
    description: "",
    outcome_type: "deliverable",
  });

  const fetchOutcomes = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter !== "ALL") params.status = statusFilter.toLowerCase();
      if (typeFilter !== "ALL") params.outcome_type = typeFilter.toLowerCase();
      const data = await outcomeService.listOutcomes(params);
      setOutcomes(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[OutcomesPage] Fetch error:", err);
      setError(err.message || "Failed to load outcomes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOutcomes();
  }, [statusFilter, typeFilter]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      setSubmitting(true);
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        outcome_type: form.outcome_type,
        status: "planned",
      };

      const res = await outcomeService.createOutcome(payload);
      setIsModalOpen(false);
      setForm({ name: "", description: "", outcome_type: "deliverable" });
      if (res?.id) {
        router.push(`/app/outcomes/${res.id}`);
      } else {
        fetchOutcomes();
      }
    } catch (err) {
      console.error("[OutcomesPage] Create error:", err);
      alert(err.message || "Failed to create outcome");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredOutcomes = outcomes.filter((o) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      o.name.toLowerCase().includes(q) ||
      (o.description && o.description.toLowerCase().includes(q))
    );
  });

  const verifiedCount = outcomes.filter((o) => o.status === "verified").length;
  const observedCount = outcomes.filter((o) => o.status === "observed").length;
  const disputedCount = outcomes.filter((o) => o.status === "disputed").length;

  const getConfidenceBadge = (confidence) => {
    switch (confidence) {
      case "verified":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">VERIFIED</Badge>;
      case "strongly_supported":
        return <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20">STRONGLY SUPPORTED</Badge>;
      case "supported":
        return <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20">SUPPORTED</Badge>;
      case "disputed":
        return <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/20">DISPUTED</Badge>;
      default:
        return <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700">UNVERIFIED</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <Award className="h-6 w-6 text-emerald-400" />
            AI Outcome Intelligence
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Tracking concrete deliverables, evidence, and verifiable impact from AI work execution.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={fetchOutcomes}
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
            New Outcome
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Outcomes"
          value={outcomes.length}
          description="Tracked deliverables & results"
          icon={<Award className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Verified"
          value={verifiedCount}
          description="Evidence-backed & approved"
          icon={<ShieldCheck className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Observed"
          value={observedCount}
          description="Execution outputs gathered"
          icon={<FileCheck className="h-5 w-5 text-blue-400" />}
        />
        <StatCard
          title="Disputed"
          value={disputedCount}
          description="Challenged outcome claims"
          icon={<AlertTriangle className="h-5 w-5 text-rose-400" />}
        />
      </div>

      {/* Filters & Search */}
      <Card className="p-4 bg-zinc-900/60 border-zinc-800">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search outcomes by deliverable name..."
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
              <option value="PLANNED">Planned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="OBSERVED">Observed</option>
              <option value="VERIFIED">Verified</option>
              <option value="DISPUTED">Disputed</option>
              <option value="FAILED">Failed</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-200"
            >
              <option value="ALL">All Types</option>
              <option value="DELIVERABLE">Deliverable</option>
              <option value="DECISION">Decision</option>
              <option value="RESOLUTION">Resolution</option>
              <option value="OPTIMIZATION">Optimization</option>
              <option value="RESEARCH_FINDING">Research Finding</option>
              <option value="AUTOMATION">Automation</option>
              <option value="SECURITY_OUTCOME">Security Outcome</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Outcomes Grid */}
      {loading ? (
        <div className="flex justify-center py-16">
          <RefreshCw className="h-8 w-8 animate-spin text-zinc-500" />
        </div>
      ) : filteredOutcomes.length === 0 ? (
        <Card className="p-12 text-center bg-zinc-900/40 border-zinc-800">
          <Award className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-zinc-300">No outcomes found</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            {searchQuery || statusFilter !== "ALL"
              ? "Try adjusting your search query or filters."
              : "Create an outcome deliverable to connect AI tasks, runs, and workflows to verifiable results."}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredOutcomes.map((o) => (
            <Link key={o.id} href={`/app/outcomes/${o.id}`}>
              <Card className="p-5 bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 transition flex flex-col justify-between h-full space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 font-mono text-[10px] uppercase">
                      {o.outcome_type}
                    </Badge>
                    {getConfidenceBadge(o.confidence)}
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-100 hover:text-indigo-300 transition line-clamp-1">
                    {o.name}
                  </h3>
                  <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
                    {o.description || "No description provided."}
                  </p>
                </div>

                <div className="space-y-2 pt-2 border-t border-zinc-800/60 text-xs text-zinc-500">
                  <div className="flex items-center justify-between font-mono text-[11px]">
                    <span>Status: <strong className="text-zinc-300 uppercase">{o.status}</strong></span>
                    {o.observed_at && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(o.observed_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create New Outcome">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Outcome Name *</label>
            <Input
              name="name"
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              placeholder="e.g. Actionable bug triage report committed to engineering backlog"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Description</label>
            <textarea
              name="description"
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              rows={3}
              placeholder="Detail the tangible deliverable, decision, or optimization..."
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Outcome Type</label>
            <select
              value={form.outcome_type}
              onChange={(e) => setForm((p) => ({ ...p, outcome_type: e.target.value }))}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
            >
              <option value="deliverable">Deliverable</option>
              <option value="decision">Decision</option>
              <option value="resolution">Resolution</option>
              <option value="optimization">Optimization</option>
              <option value="risk_reduction">Risk Reduction</option>
              <option value="issue_resolution">Issue Resolution</option>
              <option value="research_finding">Research Finding</option>
              <option value="automation">Automation</option>
              <option value="security_outcome">Security Outcome</option>
            </select>
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
              {submitting ? "Creating..." : "Create Outcome"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

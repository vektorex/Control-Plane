"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { outcomeService } from "@/services/outcomes";
import {
  Scale,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  UserCheck,
  Cpu,
  ShieldCheck,
  ArrowRight,
  Clock,
} from "lucide-react";

export default function OutcomeDecisionsPage() {
  const params = useParams();
  const outcomeId = params.outcomeId;

  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

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
      const res = await outcomeService.listDecisions({ outcomeId });
      setDecisions(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[OutcomeDecisionsPage] Error:", err);
      setError(err.message || "Failed to load decisions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (outcomeId) fetchDecisions();
  }, [outcomeId]);

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
        outcome_id: outcomeId,
      };

      await outcomeService.createDecision(payload);
      setIsModalOpen(false);
      setForm({ title: "", description: "", decision_type: "human", status: "proposed" });
      fetchDecisions();
    } catch (err) {
      console.error("[OutcomeDecisionsPage] Create decision error:", err);
      alert(err.message || "Failed to create decision");
    } finally {
      setSubmitting(false);
    }
  };

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
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/app/outcomes/${outcomeId}`}>
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Back to Outcome
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm font-semibold text-zinc-200">Work Decisions</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Propose Decision
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <Scale className="h-6 w-6 text-indigo-400" />
          Outcome Decision Governance
        </h1>
        <p className="text-sm text-zinc-400">
          Decisions affecting outcome trajectory. AI-assisted and agent decisions are strictly tracked with provenance.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-zinc-500" />
        </div>
      ) : decisions.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <Scale className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No decisions recorded</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Document key human, policy, or AI-assisted decisions that shaped this outcome.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Record First Decision
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {decisions.map((d) => (
            <Card key={d.id} className="p-5 bg-zinc-900/60 border-zinc-800 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {getDecisionBadge(d.decision_type)}
                    <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700 text-[10px] uppercase font-mono">
                      Status: {d.status}
                    </Badge>
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-100">{d.title}</h3>
                  <p className="text-xs text-zinc-400">{d.description || "No description provided."}</p>
                </div>

                <Link href={`/app/decisions/${d.id}`}>
                  <Button size="xs" variant="ghost" className="gap-1 text-indigo-400 hover:text-indigo-300">
                    Inspect Provenance <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>

              <div className="flex items-center justify-between text-[11px] text-zinc-500 font-mono pt-2 border-t border-zinc-800/80">
                <span>Decision Owner: {d.decision_owner || "system"}</span>
                <span>Created: {new Date(d.created_at).toLocaleDateString()}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Propose Decision Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Record Outcome Decision">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Decision Title *</label>
            <Input
              value={form.title}
              onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              placeholder="e.g. Approve architecture remediation proposal"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Description & Rationale</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              rows={3}
              placeholder="Explain why this decision was made and what was evaluated..."
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
              <label className="block text-xs font-medium text-zinc-300 mb-1">Initial Status</label>
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

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
  Award,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  Flame,
} from "lucide-react";

export default function ObjectiveOutcomesPage() {
  const params = useParams();
  const objectiveId = params.objectiveId;

  const [outcomes, setOutcomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: "",
    description: "",
    outcome_type: "deliverable",
  });

  const fetchOutcomes = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.listOutcomes({ objectiveId });
      setOutcomes(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[ObjectiveOutcomesPage] Error:", err);
      setError(err.message || "Failed to load outcomes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (objectiveId) fetchOutcomes();
  }, [objectiveId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;

    try {
      setSubmitting(true);
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        outcome_type: form.outcome_type,
        objective_id: objectiveId,
        status: "planned",
      };

      await outcomeService.createOutcome(payload);
      setIsModalOpen(false);
      setForm({ name: "", description: "", outcome_type: "deliverable" });
      fetchOutcomes();
    } catch (err) {
      console.error("[ObjectiveOutcomesPage] Create error:", err);
      alert(err.message || "Failed to create outcome");
    } finally {
      setSubmitting(false);
    }
  };

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
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/app/objectives/${objectiveId}`}>
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Back to Objective
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm font-semibold text-zinc-200">Outcomes</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Add Outcome
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <Award className="h-6 w-6 text-emerald-400" />
          Objective Deliverables & Outcomes
        </h1>
        <p className="text-sm text-zinc-400">
          Concrete, evidence-verified outcomes connected to this strategic objective.
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
      ) : outcomes.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <Award className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No outcomes created for this objective</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Connect deliverables, resolutions, optimizations, and decisions to track whether intended outcomes were achieved.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Add First Outcome
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {outcomes.map((o) => (
            <Card key={o.id} className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4 hover:border-zinc-700 transition">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 font-mono text-[10px] uppercase">
                      {o.outcome_type}
                    </Badge>
                    {getConfidenceBadge(o.confidence)}
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-100">{o.name}</h3>
                  <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{o.description || "No description"}</p>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-zinc-500 pt-3 border-t border-zinc-800/80">
                <span className="font-mono">Status: <strong className="text-zinc-300">{o.status}</strong></span>
                <Link href={`/app/outcomes/${o.id}`}>
                  <Button size="xs" variant="ghost" className="gap-1 text-indigo-400 hover:text-indigo-300">
                    Inspect Evidence <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Outcome Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Connected Outcome">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Outcome Name *</label>
            <Input
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="e.g. Validated competitor analysis deliverable"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Description</label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={3}
              placeholder="Describe the concrete outcome and intended impact..."
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Outcome Type</label>
            <select
              name="outcome_type"
              value={form.outcome_type}
              onChange={handleChange}
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
              <option value="approval">Approval</option>
              <option value="milestone">Milestone</option>
              <option value="customer_outcome">Customer Outcome</option>
              <option value="operational_outcome">Operational Outcome</option>
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
              {submitting ? "Saving..." : "Create Outcome"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

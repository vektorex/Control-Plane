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
  TrendingUp,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  Clock,
  DollarSign,
  ShieldCheck,
  CheckCircle2,
  FileCheck,
  Info,
} from "lucide-react";

export default function OutcomeImpactPage() {
  const params = useParams();
  const outcomeId = params.outcomeId;

  const [impactList, setImpactList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    analysis_type: "time_saved",
    summary: "",
    baseline_value: "",
    observed_value: "",
    difference_value: "",
    unit: "minutes",
    label: "observed", // observed | estimated | inferred
    limitations: "",
  });

  const fetchImpact = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.listImpact(outcomeId);
      setImpactList(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[OutcomeImpactPage] Error:", err);
      setError(err.message || "Failed to load impact analysis");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (outcomeId) fetchImpact();
  }, [outcomeId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.summary.trim()) return;

    try {
      setSubmitting(true);
      const observations = {
        baseline: form.baseline_value ? parseFloat(form.baseline_value) : null,
        observed: form.observed_value ? parseFloat(form.observed_value) : null,
        difference: form.difference_value ? parseFloat(form.difference_value) : null,
        unit: form.unit,
        attribution_label: form.label,
      };

      const payload = {
        analysis_type: form.analysis_type,
        summary: form.summary.trim(),
        observations,
        limitations: form.limitations.trim() || "Observed directly from execution timeline records.",
      };

      await outcomeService.addImpact(outcomeId, payload);
      setIsModalOpen(false);
      setForm({
        analysis_type: "time_saved",
        summary: "",
        baseline_value: "",
        observed_value: "",
        difference_value: "",
        unit: "minutes",
        label: "observed",
        limitations: "",
      });
      fetchImpact();
    } catch (err) {
      console.error("[OutcomeImpactPage] Create impact error:", err);
      alert(err.message || "Failed to record impact analysis");
    } finally {
      setSubmitting(false);
    }
  };

  const getLabelBadge = (label) => {
    switch (label) {
      case "observed":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px] uppercase font-mono">OBSERVED</Badge>;
      case "estimated":
        return <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-[10px] uppercase font-mono">ESTIMATED</Badge>;
      case "inferred":
        return <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px] uppercase font-mono">INFERRED</Badge>;
      default:
        return <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700 text-[10px] uppercase font-mono">UNVERIFIED</Badge>;
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
          <span className="text-sm font-semibold text-zinc-200">Work Impact Analysis</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Add Impact Record
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <TrendingUp className="h-6 w-6 text-emerald-400" />
          Factual Impact Analysis
        </h1>
        <p className="text-sm text-zinc-400">
          Evidence-backed comparisons only. Monetary and time savings are never fabricated without explicit baseline evidence.
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
      ) : impactList.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <TrendingUp className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No impact analyses recorded</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Record factual before-and-after observations for time, cost, quality, risk, or throughput changes.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Record First Impact
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {impactList.map((imp) => {
            const obs = imp.observations || {};
            return (
              <Card key={imp.id} className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 font-mono text-[10px] uppercase">
                        {imp.analysis_type}
                      </Badge>
                      {getLabelBadge(obs.attribution_label || "observed")}
                    </div>
                    <h3 className="text-sm font-semibold text-zinc-100">{imp.summary}</h3>
                  </div>
                </div>

                {/* Metrics Comparison Box */}
                {(obs.baseline !== undefined || obs.observed !== undefined) && (
                  <div className="grid grid-cols-3 gap-3 p-3 rounded-lg bg-zinc-950/70 border border-zinc-800/80 text-center font-mono text-xs">
                    <div>
                      <div className="text-[10px] text-zinc-500 uppercase">Baseline</div>
                      <div className="text-sm font-bold text-zinc-400 mt-0.5">
                        {obs.baseline !== null ? `${obs.baseline} ${obs.unit || ""}` : "Not recorded"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-500 uppercase">Observed</div>
                      <div className="text-sm font-bold text-zinc-100 mt-0.5">
                        {obs.observed !== null ? `${obs.observed} ${obs.unit || ""}` : "—"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-zinc-500 uppercase">Delta / Difference</div>
                      <div className="text-sm font-bold text-emerald-400 mt-0.5">
                        {obs.difference !== null ? `${obs.difference} ${obs.unit || ""}` : "—"}
                      </div>
                    </div>
                  </div>
                )}

                {imp.limitations && (
                  <div className="p-2.5 rounded bg-zinc-950/40 border border-zinc-800 text-xs text-zinc-400 flex items-start gap-2">
                    <Info className="h-3.5 w-3.5 text-zinc-500 shrink-0 mt-0.5" />
                    <span><strong>Limitations & Context:</strong> {imp.limitations}</span>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Impact Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Record Factual Impact">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Impact Type *</label>
            <select
              value={form.analysis_type}
              onChange={(e) => setForm((p) => ({ ...p, analysis_type: e.target.value }))}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
            >
              <option value="time_saved">Time Saved</option>
              <option value="cost_change">Cost Change</option>
              <option value="quality_change">Quality Change</option>
              <option value="risk_change">Risk Change</option>
              <option value="throughput_change">Throughput Change</option>
              <option value="resolution_change">Resolution Change</option>
              <option value="process_change">Process Change</option>
              <option value="operational_change">Operational Change</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Summary *</label>
            <Input
              value={form.summary}
              onChange={(e) => setForm((p) => ({ ...p, summary: e.target.value }))}
              placeholder="e.g. Incident investigation time reduced by 45 minutes"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Baseline Value</label>
              <Input
                type="number"
                step="any"
                value={form.baseline_value}
                onChange={(e) => setForm((p) => ({ ...p, baseline_value: e.target.value }))}
                placeholder="e.g. 90"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Observed Value</label>
              <Input
                type="number"
                step="any"
                value={form.observed_value}
                onChange={(e) => setForm((p) => ({ ...p, observed_value: e.target.value }))}
                placeholder="e.g. 45"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Unit</label>
              <Input
                value={form.unit}
                onChange={(e) => setForm((p) => ({ ...p, unit: e.target.value }))}
                placeholder="minutes, $, %"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Attribution Label *</label>
              <select
                value={form.label}
                onChange={(e) => setForm((p) => ({ ...p, label: e.target.value }))}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
              >
                <option value="observed">Observed (Direct measurement)</option>
                <option value="estimated">Estimated (Calculated model)</option>
                <option value="inferred">Inferred (Correlated)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Calculated Difference</label>
              <Input
                type="number"
                step="any"
                value={form.difference_value}
                onChange={(e) => setForm((p) => ({ ...p, difference_value: e.target.value }))}
                placeholder="-45"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Limitations & Scope</label>
            <textarea
              value={form.limitations}
              onChange={(e) => setForm((p) => ({ ...p, limitations: e.target.value }))}
              rows={2}
              placeholder="State any caveats, assumptions, or sample size limits..."
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
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
              {submitting ? "Saving..." : "Save Impact"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

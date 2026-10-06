"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { outcomeService } from "@/services/outcomes";
import {
  Award,
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  FileCheck,
  CheckCircle2,
  Clock,
  Layers,
  GitPullRequest,
  Scale,
  Activity,
  RefreshCw,
  Plus,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export default function OutcomeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const outcomeId = params.outcomeId;

  const [outcome, setOutcome] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  const [measurements, setMeasurements] = useState([]);
  const [workLinks, setWorkLinks] = useState([]);
  const [attributions, setAttributions] = useState([]);
  const [impactList, setImpactList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Verification modal state
  const [isVerifyOpen, setIsVerifyOpen] = useState(false);
  const [isDisputeOpen, setIsDisputeOpen] = useState(false);
  const [disputeReason, setDisputeReason] = useState("");
  const [verifying, setVerifying] = useState(false);

  // Measurement modal state
  const [isMeasureOpen, setIsMeasureOpen] = useState(false);
  const [measureForm, setMeasureForm] = useState({
    metric_name: "",
    value: "",
    unit: "",
    measurement_source: "system",
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [outData, evData, msData, wkData, atData, impData] = await Promise.allSettled([
        outcomeService.getOutcome(outcomeId),
        outcomeService.listEvidence(outcomeId),
        outcomeService.listMeasurements(outcomeId),
        outcomeService.listWorkLinks(outcomeId),
        outcomeService.listAttributions(outcomeId),
        outcomeService.listImpact(outcomeId),
      ]);

      if (outData.status === "fulfilled") {
        setOutcome(outData.value);
      } else {
        throw new Error(outData.reason?.message || "Failed to load outcome");
      }

      if (evData.status === "fulfilled") setEvidenceList(evData.value || []);
      if (msData.status === "fulfilled") setMeasurements(msData.value || []);
      if (wkData.status === "fulfilled") setWorkLinks(wkData.value || []);
      if (atData.status === "fulfilled") setAttributions(atData.value || []);
      if (impData.status === "fulfilled") setImpactList(impData.value || []);
    } catch (err) {
      console.error("[OutcomeDetailPage] Error:", err);
      setError(err.message || "Failed to load outcome details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (outcomeId) fetchData();
  }, [outcomeId]);

  const handleVerify = async () => {
    try {
      setVerifying(true);
      await outcomeService.verifyOutcome(outcomeId, {
        notes: "Human verification confirmed through outcome intelligence dashboard.",
      });
      setIsVerifyOpen(false);
      fetchData();
    } catch (err) {
      console.error("[OutcomeDetailPage] Verify failed:", err);
      alert(err.message || "Outcome verification failed. Ensure required evidence is attached.");
    } finally {
      setVerifying(false);
    }
  };

  const handleDispute = async (e) => {
    e.preventDefault();
    if (!disputeReason.trim()) return;

    try {
      setVerifying(true);
      await outcomeService.disputeOutcome(outcomeId, { reason: disputeReason.trim() });
      setIsDisputeOpen(false);
      setDisputeReason("");
      fetchData();
    } catch (err) {
      console.error("[OutcomeDetailPage] Dispute failed:", err);
      alert(err.message || "Failed to dispute outcome");
    } finally {
      setVerifying(false);
    }
  };

  const handleAddMeasurement = async (e) => {
    e.preventDefault();
    if (!measureForm.metric_name.trim() || !measureForm.value) return;

    try {
      await outcomeService.addMeasurement(outcomeId, {
        metric_name: measureForm.metric_name.trim(),
        value: parseFloat(measureForm.value),
        unit: measureForm.unit.trim() || null,
        measurement_source: measureForm.measurement_source,
      });
      setIsMeasureOpen(false);
      setMeasureForm({ metric_name: "", value: "", unit: "", measurement_source: "system" });
      fetchData();
    } catch (err) {
      console.error("[OutcomeDetailPage] Add measurement failed:", err);
      alert(err.message || "Failed to record measurement");
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-emerald-400" />
        <p className="text-sm text-zinc-400">Loading outcome intelligence...</p>
      </div>
    );
  }

  if (error || !outcome) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Link href="/app/outcomes">
          <Button variant="ghost" size="sm" className="gap-2 text-zinc-400">
            <ArrowLeft className="h-4 w-4" /> Back to Outcomes
          </Button>
        </Link>
        <Card className="p-8 text-center bg-rose-500/5 border-rose-500/20 text-rose-400">
          <AlertTriangle className="h-10 w-10 mx-auto mb-2 text-rose-400" />
          <h2 className="text-lg font-bold">Outcome Not Found or Error</h2>
          <p className="text-sm text-zinc-400 mt-1">{error || "Could not retrieve outcome data"}</p>
        </Card>
      </div>
    );
  }

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

  const humanEvidenceCount = evidenceList.filter((e) => e.evidence_type === "human_confirmation").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Breadcrumb & Action Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app/outcomes">
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Outcomes
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm text-zinc-300 font-mono">{outcome.id.slice(0, 8)}...</span>
        </div>
        <div className="flex items-center gap-2">
          {outcome.status !== "verified" && (
            <Button
              onClick={() => setIsVerifyOpen(true)}
              size="sm"
              className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Verify Outcome
            </Button>
          )}
          {outcome.status !== "disputed" && (
            <Button
              onClick={() => setIsDisputeOpen(true)}
              variant="outline"
              size="sm"
              className="gap-2 border-rose-900/50 text-rose-400 hover:bg-rose-950/20"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Dispute
            </Button>
          )}
          <Button
            onClick={fetchData}
            variant="outline"
            size="sm"
            className="border-zinc-800 text-zinc-300"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Main Header Card */}
      <Card className="p-6 bg-zinc-900/60 border-zinc-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 font-mono text-[10px] uppercase">
                {outcome.outcome_type}
              </Badge>
              <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 font-mono text-[10px] uppercase">
                Status: {outcome.status}
              </Badge>
              {getConfidenceBadge(outcome.confidence)}
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              {outcome.name}
            </h1>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {outcome.description || "No description provided."}
            </p>
          </div>

          <div className="flex flex-col sm:items-end gap-2 text-xs text-zinc-400 shrink-0 font-mono">
            {outcome.observed_at && (
              <div className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-zinc-500" />
                Observed: {new Date(outcome.observed_at).toLocaleDateString()}
              </div>
            )}
            {outcome.objective_id && (
              <Link href={`/app/objectives/${outcome.objective_id}`}>
                <div className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300">
                  <Target className="h-3.5 w-3.5" />
                  View Strategic Objective
                </div>
              </Link>
            )}
          </div>
        </div>

        {/* Sub Navigation Bar */}
        <div className="flex items-center gap-2 pt-2 border-t border-zinc-800/80 overflow-x-auto">
          <Link href={`/app/outcomes/${outcome.id}`}>
            <Button variant="ghost" size="sm" className="text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 text-xs">
              Overview
            </Button>
          </Link>
          <Link href={`/app/outcomes/${outcome.id}/evidence`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Evidence ({evidenceList.length})
            </Button>
          </Link>
          <Link href={`/app/outcomes/${outcome.id}/work`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Linked Work ({workLinks.length})
            </Button>
          </Link>
          <Link href={`/app/outcomes/${outcome.id}/impact`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Impact Analysis ({impactList.length})
            </Button>
          </Link>
          <Link href={`/app/outcomes/${outcome.id}/decisions`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Decisions
            </Button>
          </Link>
          <Link href={`/app/outcomes/${outcome.id}/graph`}>
            <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-zinc-200 text-xs">
              Attribution Graph
            </Button>
          </Link>
        </div>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Evidence Items"
          value={evidenceList.length}
          description={`${humanEvidenceCount} human-confirmed`}
          icon={<ShieldCheck className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Factual Measurements"
          value={measurements.length}
          description="Observed metric points"
          icon={<FileCheck className="h-5 w-5 text-blue-400" />}
        />
        <StatCard
          title="Work Resources"
          value={workLinks.length}
          description="Tasks, Runs, Workflows linked"
          icon={<Layers className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Attribution Confidence"
          value={outcome.confidence.toUpperCase()}
          description="Evidence-backed state"
          icon={<Award className="h-5 w-5 text-amber-400" />}
        />
      </div>

      {/* Grid: Measurements & Attributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Factual Measurements */}
        <Card className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2">
              <FileCheck className="h-4 w-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-zinc-200">Factual Measurements</h3>
            </div>
            <Button
              onClick={() => setIsMeasureOpen(true)}
              size="xs"
              className="gap-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs"
            >
              <Plus className="h-3 w-3" /> Add Measurement
            </Button>
          </div>

          {measurements.length === 0 ? (
            <div className="text-center py-6 text-zinc-500 text-xs">
              No factual measurements recorded yet for this outcome.
            </div>
          ) : (
            <div className="space-y-2">
              {measurements.map((m) => (
                <div key={m.id} className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/40 flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="font-semibold text-zinc-200">{m.metric_name}</span>
                    <div className="text-[10px] text-zinc-500 font-sans">
                      Source: {m.measurement_source}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-indigo-400 text-sm">{m.value}</span>
                    {m.unit && <span className="text-zinc-400 text-xs ml-1">{m.unit}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Outcome Attributions */}
        <Card className="p-5 bg-zinc-900/60 border-zinc-800 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2">
              <GitPullRequest className="h-4 w-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-zinc-200">Resource Attributions</h3>
            </div>
            <Link href={`/app/outcomes/${outcome.id}/graph`}>
              <Button size="xs" variant="ghost" className="gap-1 text-xs text-indigo-400 hover:text-indigo-300">
                View Graph <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>

          {attributions.length === 0 ? (
            <div className="text-center py-6 text-zinc-500 text-xs">
              No attributions recorded yet. (Never claims direct causation without factual proof).
            </div>
          ) : (
            <div className="space-y-2">
              {attributions.map((at) => (
                <div key={at.id} className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/40 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-zinc-300">
                      {at.resource_type}: {at.resource_id.slice(0, 10)}...
                    </span>
                    <Badge className="text-[10px] bg-zinc-800 text-indigo-300 border-zinc-700 uppercase">
                      {at.attribution_type}
                    </Badge>
                  </div>
                  {at.explanation && (
                    <p className="text-xs text-zinc-400">{at.explanation}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Verify Confirmation Modal */}
      <Modal isOpen={isVerifyOpen} onClose={() => setIsVerifyOpen(false)} title="Verify Outcome Deliverable">
        <div className="space-y-4 text-xs text-zinc-300">
          <p>
            You are marking outcome deliverable <strong className="text-zinc-100">{outcome.name}</strong> as VERIFIED.
          </p>
          <div className="p-3 rounded bg-zinc-950 border border-zinc-800 space-y-1">
            <div className="text-[11px] font-semibold text-zinc-200">Deterministic Pre-Flight Checks:</div>
            <div className="flex items-center gap-2 text-emerald-400 text-xs">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Evidence present: {evidenceList.length} items recorded
            </div>
            <div className="text-xs text-zinc-400">
              Human sign-off will be recorded in immutable audit logs.
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-zinc-800">
            <Button variant="ghost" size="sm" onClick={() => setIsVerifyOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleVerify}
              disabled={verifying}
              className="bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              {verifying ? "Verifying..." : "Confirm Verification"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Dispute Modal */}
      <Modal isOpen={isDisputeOpen} onClose={() => setIsDisputeOpen(false)} title="Dispute Outcome Claim">
        <form onSubmit={handleDispute} className="space-y-4">
          <p className="text-xs text-zinc-400">
            Provide the factual rationale for challenging this outcome claim.
          </p>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Reason for Dispute *</label>
            <textarea
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              rows={3}
              placeholder="Explain why this deliverable or outcome failed to meet its criteria..."
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-rose-500"
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-zinc-800">
            <Button variant="ghost" size="sm" onClick={() => setIsDisputeOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={verifying}
              className="bg-rose-600 hover:bg-rose-500 text-white"
            >
              {verifying ? "Disputing..." : "Submit Dispute"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Measurement Modal */}
      <Modal isOpen={isMeasureOpen} onClose={() => setIsMeasureOpen(false)} title="Add Factual Measurement">
        <form onSubmit={handleAddMeasurement} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Metric Name *</label>
            <Input
              value={measureForm.metric_name}
              onChange={(e) => setMeasureForm((p) => ({ ...p, metric_name: e.target.value }))}
              placeholder="e.g. issues_resolved, review_duration_minutes"
              className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs font-mono"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Value *</label>
              <Input
                type="number"
                step="any"
                value={measureForm.value}
                onChange={(e) => setMeasureForm((p) => ({ ...p, value: e.target.value }))}
                placeholder="e.g. 42"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Unit</label>
              <Input
                value={measureForm.unit}
                onChange={(e) => setMeasureForm((p) => ({ ...p, unit: e.target.value }))}
                placeholder="e.g. min, count, %"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Measurement Source</label>
            <select
              value={measureForm.measurement_source}
              onChange={(e) => setMeasureForm((p) => ({ ...p, measurement_source: e.target.value }))}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
            >
              <option value="system">System</option>
              <option value="workflow">Workflow</option>
              <option value="evaluation">Evaluation Lab</option>
              <option value="event">Event Bus</option>
              <option value="artifact">Artifact</option>
              <option value="connector">Connector</option>
              <option value="manual">Manual</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-zinc-800">
            <Button variant="ghost" size="sm" onClick={() => setIsMeasureOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-500 text-white">
              Save Measurement
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

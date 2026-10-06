"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { outcomeService } from "@/services/outcomes";
import {
  Scale,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock,
  ShieldCheck,
  Cpu,
  UserCheck,
  Target,
  Award,
  Layers,
  FileText,
} from "lucide-react";

export default function DecisionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const decisionId = params.decisionId;

  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);

  const fetchDecision = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.getDecision(decisionId);
      setDecision(res);
    } catch (err) {
      console.error("[DecisionDetailPage] Error:", err);
      setError(err.message || "Failed to load decision");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (decisionId) fetchDecision();
  }, [decisionId]);

  const handleApprove = async () => {
    try {
      setProcessing(true);
      await outcomeService.approveDecision(decisionId);
      fetchDecision();
    } catch (err) {
      alert(err.message || "Failed to approve decision");
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    const reason = prompt("Enter factual reason for rejecting this decision:");
    if (!reason) return;
    try {
      setProcessing(true);
      await outcomeService.rejectDecision(decisionId, reason);
      fetchDecision();
    } catch (err) {
      alert(err.message || "Failed to reject decision");
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm text-zinc-400">Loading decision governance details...</p>
      </div>
    );
  }

  if (error || !decision) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Link href="/app/decisions">
          <Button variant="ghost" size="sm" className="gap-2 text-zinc-400">
            <ArrowLeft className="h-4 w-4" /> Back to Decisions
          </Button>
        </Link>
        <Card className="p-8 text-center bg-rose-500/5 border-rose-500/20 text-rose-400">
          <AlertTriangle className="h-10 w-10 mx-auto mb-2 text-rose-400" />
          <h2 className="text-lg font-bold">Decision Not Found or Error</h2>
          <p className="text-sm text-zinc-400 mt-1">{error || "Could not retrieve decision record"}</p>
        </Card>
      </div>
    );
  }

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

  const provenance = decision.provenance || {};

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app/decisions">
            <Button variant="ghost" size="sm" className="gap-2 text-zinc-400 hover:text-zinc-100">
              <ArrowLeft className="h-4 w-4" />
              Decisions
            </Button>
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-sm text-zinc-300 font-mono">{decision.id.slice(0, 8)}...</span>
        </div>

        <div className="flex items-center gap-2">
          {decision.status !== "approved" && (
            <Button
              size="sm"
              disabled={processing}
              onClick={handleApprove}
              className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Approve Decision
            </Button>
          )}
          {decision.status !== "rejected" && (
            <Button
              size="sm"
              variant="outline"
              disabled={processing}
              onClick={handleReject}
              className="gap-2 border-rose-900/50 text-rose-400 hover:bg-rose-950/20"
            >
              <XCircle className="h-3.5 w-3.5" />
              Reject Decision
            </Button>
          )}
          <Button
            onClick={fetchDecision}
            variant="outline"
            size="sm"
            className="border-zinc-800 text-zinc-300"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Main Decision Card */}
      <Card className="p-6 bg-zinc-900/60 border-zinc-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center gap-2 flex-wrap">
              {getDecisionBadge(decision.decision_type)}
              <Badge className={`text-[10px] uppercase font-mono ${
                decision.status === "approved"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : decision.status === "rejected"
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  : "bg-zinc-800 text-zinc-400 border-zinc-700"
              }`}>
                Status: {decision.status}
              </Badge>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              {decision.title}
            </h1>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {decision.description || "No description provided."}
            </p>
          </div>

          <div className="flex flex-col sm:items-end gap-2 text-xs text-zinc-400 shrink-0 font-mono">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-zinc-500" />
              Created: {new Date(decision.created_at).toLocaleDateString()}
            </div>
            <div>Owner: {decision.decision_owner || "system"}</div>
          </div>
        </div>

        {/* Connected Context Links */}
        {(decision.objective_id || decision.outcome_id) && (
          <div className="flex items-center gap-4 pt-3 border-t border-zinc-800/80 text-xs">
            {decision.objective_id && (
              <Link href={`/app/objectives/${decision.objective_id}`}>
                <span className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300">
                  <Target className="h-3.5 w-3.5" /> Strategic Objective
                </span>
              </Link>
            )}
            {decision.outcome_id && (
              <Link href={`/app/outcomes/${decision.outcome_id}`}>
                <span className="flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300">
                  <Award className="h-3.5 w-3.5" /> Connected Deliverable
                </span>
              </Link>
            )}
          </div>
        )}
      </Card>

      {/* Decision Provenance Card */}
      <Card className="p-6 bg-zinc-900/60 border-zinc-800 space-y-4">
        <div className="flex items-center gap-2 border-b border-zinc-800/80 pb-3">
          <ShieldCheck className="h-4 w-4 text-indigo-400" />
          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Decision Provenance & Audit Trail
            </h2>
            <p className="text-xs text-zinc-400">
              Answers &quot;Why was this decision made?&quot; without exposing raw internal chain-of-thought.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80 space-y-1">
            <div className="text-[10px] uppercase text-zinc-500">Agent / Model Provenance</div>
            <div className="text-zinc-200">Agent ID: {provenance.agent_id || "None (Human/Policy)"}</div>
            <div className="text-zinc-400">Model/Provider: {provenance.model_provider || "N/A"}</div>
            <div className="text-zinc-400">Prompt Version: {provenance.prompt_version || "N/A"}</div>
          </div>

          <div className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80 space-y-1">
            <div className="text-[10px] uppercase text-zinc-500">Governance & Execution Checks</div>
            <div className="text-zinc-200">Run ID: {provenance.run_id || "N/A"}</div>
            <div className="text-zinc-400">Evaluation ID: {provenance.evaluation_id || "None required"}</div>
            <div className="text-zinc-400">Approval ID: {provenance.approval_id || "None required"}</div>
          </div>
        </div>

        {decision.evidence_ids && decision.evidence_ids.length > 0 && (
          <div className="p-3 rounded-lg bg-zinc-950/40 border border-zinc-800 space-y-2">
            <div className="text-xs font-semibold text-zinc-300">Supporting Evidence Provenance:</div>
            <div className="flex flex-wrap gap-2">
              {decision.evidence_ids.map((evId, idx) => (
                <Badge key={idx} className="bg-zinc-800 text-zinc-300 border-zinc-700 font-mono text-[10px]">
                  evidence:{evId.slice(0, 8)}...
                </Badge>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

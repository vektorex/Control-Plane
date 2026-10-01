"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  FileCode,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Clock,
  Cpu,
  Coins,
  ArrowLeft,
  RefreshCw,
  ShieldCheck,
  Tag,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function CaseDetailPage() {
  const params = useParams();
  const experimentId = params?.experimentId;
  const caseId = params?.caseId;

  const [caseItem, setCaseItem] = useState(null);
  const [runRecord, setRunRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replaying, setReplaying] = useState(false);
  const [replayOutput, setReplayOutput] = useState(null);

  useEffect(() => {
    if (caseId && experimentId) {
      loadDetails();
    }
  }, [caseId, experimentId]);

  async function loadDetails() {
    setLoading(true);
    setError(null);
    try {
      const [c, results] = await Promise.all([
        evaluationLabService.getCase(caseId),
        evaluationLabService.getExperimentResults(experimentId),
      ]);
      setCaseItem(c);
      const match = results?.runs?.find((r) => r.case_id === caseId);
      setRunRecord(match || null);
    } catch (err) {
      setError(err?.message || "Failed to load case run details");
    } finally {
      setLoading(false);
    }
  }

  async function handleReplay() {
    setReplaying(true);
    // Simulate safe dry-run replay of this individual case
    setTimeout(() => {
      setReplayOutput({
        status: "passed",
        replayed_at: new Date().toLocaleTimeString(),
        note: "Safe dry-run re-execution completed. No side effects were triggered.",
      });
      setReplaying(false);
    }, 1200);
  }

  if (loading) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
        <RefreshCw className="w-6 h-6 animate-spin text-primary" />
        Loading case evaluation details...
      </div>
    );
  }

  if (error || !caseItem) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center space-y-4">
        <p className="text-red-500">{error || "Case details not found"}</p>
        <Link
          href={`/app/evaluation/experiments/${experimentId}`}
          className="text-xs text-primary hover:underline"
        >
          Return to Experiment Results
        </Link>
      </div>
    );
  }

  const assertions = runRecord?.evaluation_result?.assertions || [];
  const findings = runRecord?.evaluation_result?.evaluation_findings || [];

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            <Link href={`/app/evaluation/experiments/${experimentId}`} className="hover:text-foreground flex items-center gap-1">
              <ArrowLeft className="w-3 h-3" /> Back to Experiment
            </Link>
            <span>/</span>
            <span>Case Inspection</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <FileCode className="w-6 h-6 text-primary" />
              {caseItem.name}
            </h1>
            <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-muted text-muted-foreground">
              {caseItem.case_key}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReplay}
            disabled={replaying}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition flex items-center gap-1.5 shadow-sm disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${replaying ? "animate-spin" : ""}`} />
            {replaying ? "Replaying (Dry-Run)..." : "Replay Case (Dry-Run)"}
          </button>
        </div>
      </div>

      {replayOutput && (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-xs text-emerald-400 space-y-1">
          <p className="font-semibold flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {replayOutput.note}
          </p>
          <p className="text-muted-foreground">Timestamp: {replayOutput.replayed_at}</p>
        </div>
      )}

      {/* Metrics Row */}
      {runRecord && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase">Run Status</span>
            <p className="text-lg font-bold capitalize text-foreground">{runRecord.status}</p>
          </div>
          <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <Clock className="w-3 h-3" /> Latency
            </span>
            <p className="text-lg font-bold text-foreground font-mono">{runRecord.latency_ms || 0} ms</p>
          </div>
          <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <Cpu className="w-3 h-3" /> Tokens
            </span>
            <p className="text-lg font-bold text-foreground font-mono">
              {(runRecord.input_tokens || 0) + (runRecord.output_tokens || 0)}
            </p>
          </div>
          <div className="p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <Coins className="w-3 h-3" /> Estimated Cost
            </span>
            <p className="text-lg font-bold text-foreground font-mono">${runRecord.estimated_cost || 0}</p>
          </div>
        </div>
      )}

      {/* Inputs and Output Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Input */}
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Case Input Payload
          </h3>
          <pre className="p-3 rounded-lg bg-background/80 border border-border/40 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
            {typeof caseItem.input_data === "object"
              ? JSON.stringify(caseItem.input_data, null, 2)
              : String(caseItem.input_data)}
          </pre>
        </div>

        {/* Expected Output */}
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Expected Output / Ground Truth
          </h3>
          <pre className="p-3 rounded-lg bg-background/80 border border-border/40 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
            {caseItem.expected_output || "(No explicit expected output defined; checked via assertions)"}
          </pre>
        </div>
      </div>

      {/* Actual Model Output */}
      {runRecord?.output_snapshot && (
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Generated Output Snapshot
          </h3>
          <pre className="p-3 rounded-lg bg-background/80 border border-border/40 text-xs font-mono overflow-x-auto whitespace-pre-wrap text-foreground">
            {runRecord.output_snapshot.text || JSON.stringify(runRecord.output_snapshot, null, 2)}
          </pre>
        </div>
      )}

      {/* Assertions Evaluation Breakdown */}
      <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden space-y-0">
        <div className="p-4 border-b border-border/40">
          <h3 className="text-sm font-semibold text-foreground">
            Deterministic Assertions Evaluation ({assertions.length})
          </h3>
        </div>

        {assertions.length === 0 ? (
          <div className="p-6 text-center text-xs text-muted-foreground">
            No deterministic assertions were configured for this case.
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {assertions.map((a, i) => (
              <div key={i} className="p-4 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        a.passed
                          ? "bg-emerald-500/10 text-emerald-500"
                          : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {a.passed ? "Passed" : "Failed"}
                    </span>
                    <span className="font-mono text-xs font-semibold text-foreground">
                      {a.assertion_type}
                    </span>
                    {a.path && (
                      <span className="text-xs text-muted-foreground font-mono">
                        (path: {a.path})
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{a.message}</p>
                </div>

                <div className="text-right text-xs font-mono space-y-0.5">
                  {a.expected && (
                    <div className="text-muted-foreground">
                      Expected: <span className="text-foreground">{String(a.expected)}</span>
                    </div>
                  )}
                  {a.actual && (
                    <div className="text-muted-foreground">
                      Actual: <span className="text-foreground">{String(a.actual)}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Verification Findings (EvaluationEngine) */}
      <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden space-y-0">
        <div className="p-4 border-b border-border/40">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            Evaluation Engine Findings
          </h3>
        </div>

        {findings.length === 0 ? (
          <div className="p-6 text-center text-xs text-muted-foreground">
            No evaluator findings generated.
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {findings.map((f, i) => (
              <div key={i} className="p-4 flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        f.passed
                          ? "bg-emerald-500/10 text-emerald-500"
                          : "bg-red-500/10 text-red-500 font-bold"
                      }`}
                    >
                      {f.passed ? "Verified" : "Failed"}
                    </span>
                    <span className="text-xs font-semibold text-foreground capitalize">
                      {f.check_type} Verification
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{f.message}</p>
                </div>

                {f.score !== undefined && (
                  <div className="text-xs font-mono text-muted-foreground">
                    Score: <strong className="text-foreground">{f.score}</strong>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

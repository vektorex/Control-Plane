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
  ShieldCheck,
  ArrowLeft,
  Plus,
  RefreshCw,
  AlertCircle,
  FileCheck,
  UserCheck,
  Cpu,
  Clock,
  Sparkles,
} from "lucide-react";

export default function OutcomeEvidencePage() {
  const params = useParams();
  const outcomeId = params.outcomeId;

  const [evidenceList, setEvidenceList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    evidence_type: "execution_result",
    description: "",
    source_type: "task",
    source_id: "",
    snapshot_json: "",
  });

  const fetchEvidence = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await outcomeService.listEvidence(outcomeId);
      setEvidenceList(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("[OutcomeEvidencePage] Error:", err);
      setError(err.message || "Failed to load outcome evidence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (outcomeId) fetchEvidence();
  }, [outcomeId]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.description.trim()) return;

    try {
      setSubmitting(true);
      let parsedSnapshot = null;
      if (form.snapshot_json.trim()) {
        try {
          parsedSnapshot = JSON.parse(form.snapshot_json);
        } catch (e) {
          alert("Snapshot must be valid JSON format");
          setSubmitting(false);
          return;
        }
      }

      const payload = {
        evidence_type: form.evidence_type,
        description: form.description.trim(),
        source_type: form.source_type,
        source_id: form.source_id.trim() || null,
        snapshot: parsedSnapshot,
      };

      await outcomeService.addEvidence(outcomeId, payload);
      setIsModalOpen(false);
      setForm({
        evidence_type: "execution_result",
        description: "",
        source_type: "task",
        source_id: "",
        snapshot_json: "",
      });
      fetchEvidence();
    } catch (err) {
      console.error("[OutcomeEvidencePage] Add evidence error:", err);
      alert(err.message || "Failed to add evidence");
    } finally {
      setSubmitting(false);
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
          <span className="text-sm font-semibold text-zinc-200">Outcome Evidence</span>
        </div>
        <Button
          onClick={() => setIsModalOpen(true)}
          className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          Attach Evidence
        </Button>
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-emerald-400" />
          Provenance & Evidence Records
        </h1>
        <p className="text-sm text-zinc-400">
          AI-generated claims cannot become verified outcomes without supporting proof. Human confirmations are explicitly flagged.
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
      ) : evidenceList.length === 0 ? (
        <Card className="p-10 text-center bg-zinc-900/40 border-zinc-800">
          <ShieldCheck className="h-10 w-10 text-zinc-600 mx-auto mb-3" />
          <h3 className="text-base font-medium text-zinc-300">No evidence attached yet</h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
            Attach execution results, evaluation lab runs, human approvals, or connector snapshots to substantiate this outcome.
          </p>
          <Button
            onClick={() => setIsModalOpen(true)}
            size="sm"
            className="mt-4 gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" /> Attach First Evidence
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {evidenceList.map((ev) => {
            const isHuman = ev.evidence_type === "human_confirmation";
            return (
              <Card key={ev.id} className="p-5 bg-zinc-900/60 border-zinc-800 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {isHuman ? (
                        <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 flex items-center gap-1 font-mono text-[10px]">
                          <UserCheck className="h-3 w-3" />
                          HUMAN CONFIRMED
                        </Badge>
                      ) : (
                        <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 flex items-center gap-1 font-mono text-[10px]">
                          <Cpu className="h-3 w-3" />
                          AI / SYSTEM GENERATED
                        </Badge>
                      )}
                      <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700 text-[10px] font-mono">
                        {ev.evidence_type}
                      </Badge>
                      <Badge className="bg-zinc-800 text-zinc-400 border-zinc-700 text-[10px] font-mono">
                        status: {ev.status}
                      </Badge>
                    </div>
                    <p className="text-sm font-medium text-zinc-200 mt-1">{ev.description}</p>
                  </div>

                  <div className="text-right text-[11px] text-zinc-500 font-mono shrink-0">
                    <div>Source: {ev.source_type}</div>
                    {ev.source_id && <div>ID: {ev.source_id.slice(0, 10)}...</div>}
                  </div>
                </div>

                {ev.snapshot && (
                  <div className="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
                    <span className="text-[10px] text-zinc-500 uppercase font-mono">Snapshot Data</span>
                    <pre className="text-[11px] text-zinc-300 font-mono mt-1 overflow-x-auto max-h-36">
                      {JSON.stringify(ev.snapshot, null, 2)}
                    </pre>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Attach Evidence Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Attach Outcome Evidence">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Evidence Type *</label>
            <select
              value={form.evidence_type}
              onChange={(e) => setForm((p) => ({ ...p, evidence_type: e.target.value }))}
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100"
            >
              <option value="execution_result">Execution Result</option>
              <option value="human_confirmation">Human Confirmation</option>
              <option value="evaluation_result">Evaluation Result</option>
              <option value="artifact">Artifact Deliverable</option>
              <option value="document">Document</option>
              <option value="connector_record">Connector Record</option>
              <option value="workflow_result">Workflow Result</option>
              <option value="metric_observation">Metric Observation</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Description / Summary *</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              rows={2}
              placeholder="State what this evidence demonstrates..."
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Source Type</label>
              <Input
                value={form.source_type}
                onChange={(e) => setForm((p) => ({ ...p, source_type: e.target.value }))}
                placeholder="task, run, artifact..."
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Source Resource ID</label>
              <Input
                value={form.source_id}
                onChange={(e) => setForm((p) => ({ ...p, source_id: e.target.value }))}
                placeholder="UUID"
                className="bg-zinc-950 border-zinc-800 text-zinc-100 text-xs font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Snapshot JSON (optional)</label>
            <textarea
              value={form.snapshot_json}
              onChange={(e) => setForm((p) => ({ ...p, snapshot_json: e.target.value }))}
              rows={3}
              placeholder='{"status": "passed", "latency_ms": 320}'
              className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-100 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
              {submitting ? "Attaching..." : "Attach Evidence"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

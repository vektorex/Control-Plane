"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Plus, RefreshCw, Trash2, Play } from "lucide-react";
import { securityService } from "@/services/security";
import { PlaybookModal } from "@/components/features/security/PlaybookModal";

export default function SecurityPlaybooksPage() {
  const [playbooks, setPlaybooks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMsg("");
      const res = await securityService.listPlaybooks({ limit: 100 });
      setPlaybooks(res?.items || []);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load playbooks.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this response playbook?")) return;
    try {
      await securityService.deletePlaybook(id);
      fetchData();
    } catch (err) {
      alert("Failed to delete playbook: " + (err.message || err));
    }
  };

  const handleTestPlaybook = async (pb) => {
    try {
      const res = await securityService.testPlaybook(pb.id, {
        signal_type: pb.trigger_conditions?.signal_type || "prompt_injection",
        severity: pb.trigger_conditions?.min_severity || "high",
      });
      setTestResult({ id: pb.id, ...res });
    } catch (err) {
      alert("Failed to dry-run playbook: " + (err.message || err));
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/app/security"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-emerald-400" />
              Response Playbooks
            </h1>
            <p className="text-xs text-slate-400">
              Deterministic incident response playbooks with strictly allowlisted containment actions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchData()}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            New Playbook
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-xs text-red-300">
          {errorMsg}
        </div>
      )}

      {playbooks.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-xs">
          No response playbooks configured yet. Click &quot;New Playbook&quot; to configure automated response rules.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {playbooks.map((pb) => (
            <div
              key={pb.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 shadow-sm hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">{pb.name}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    {pb.enabled ? "Active" : "Disabled"}
                  </span>
                  <button
                    onClick={() => handleDelete(pb.id)}
                    className="p-1 rounded text-slate-500 hover:text-red-400"
                    title="Delete Playbook"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {pb.description && (
                <p className="text-xs text-slate-400">{pb.description}</p>
              )}

              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-1.5">
                <div className="text-slate-500">
                  Trigger Conditions:{" "}
                  <span className="font-mono text-slate-300">
                    {JSON.stringify(pb.trigger_conditions)}
                  </span>
                </div>
                <div className="text-slate-500">
                  Allowlisted Actions:{" "}
                  <span className="font-mono text-indigo-400">
                    {Array.isArray(pb.actions) ? pb.actions.join(", ") : pb.actions}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => handleTestPlaybook(pb)}
                  className="px-2.5 py-1 text-xs rounded border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center gap-1.5"
                >
                  <Play className="w-3 h-3 text-emerald-400" />
                  Dry-Run Test
                </button>

                {testResult?.id === pb.id && (
                  <span className="text-[11px] text-emerald-400 font-mono">
                    Simulation Passed: {testResult.simulated_actions?.length || 0} action(s) matched
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <PlaybookModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => fetchData()}
      />
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  Bookmark,
  Play,
  Clock,
  Eye,
  CheckCircle,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { ResumeModal } from "./ResumeModal";

export function ExecutionCheckpointTable({ checkpoints = [], onRefresh }) {
  const [selectedCheckpoint, setSelectedCheckpoint] = useState(null);
  const [inspectCheckpoint, setInspectCheckpoint] = useState(null);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Bookmark className="w-4 h-4 text-blue-400" />
            Execution Checkpoints ({checkpoints.length})
          </h3>
          <p className="text-xs text-slate-500">
            Sanitized, bounded state snapshots enabling safe recovery without duplicate side effects.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 font-semibold">Run ID</th>
              <th className="py-3 px-4 font-semibold">Step / Seq</th>
              <th className="py-3 px-4 font-semibold">Checkpoint Type</th>
              <th className="py-3 px-4 font-semibold">Input Hash</th>
              <th className="py-3 px-4 font-semibold">Created At</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {checkpoints.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                  No active execution checkpoints recorded.
                </td>
              </tr>
            ) : (
              checkpoints.map((cp) => (
                <tr key={cp.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-mono text-xs font-semibold text-white">
                      {cp.run_id}
                    </div>
                    {cp.workflow_run_id && (
                      <div className="text-[11px] font-mono text-slate-500">
                        wf: {cp.workflow_run_id}
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-medium text-slate-200">
                      {cp.step_id || "step_init"}
                    </span>
                    <span className="text-slate-500 text-[11px] ml-1.5 font-mono">
                      (#{cp.sequence_number})
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300 font-mono">
                      {cp.checkpoint_type}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <code className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {cp.input_fingerprint ? cp.input_fingerprint.substring(0, 12) + "..." : "-"}
                    </code>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(cp.created_at).toLocaleTimeString()}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => setInspectCheckpoint(cp)}
                      className="p-1 rounded text-slate-400 hover:text-white"
                      title="Inspect Snapshot"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setSelectedCheckpoint(cp)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                    >
                      <RotateCcw className="w-3 h-3" /> Resume
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Snapshot Inspector Modal */}
      {inspectCheckpoint && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 space-y-4 shadow-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">Checkpoint State Snapshot</h3>
                <p className="text-xs font-mono text-slate-500">{inspectCheckpoint.id}</p>
              </div>
              <button
                onClick={() => setInspectCheckpoint(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 text-xs font-mono overflow-x-auto">
              {JSON.stringify(inspectCheckpoint.state_snapshot, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Resume execution modal */}
      {selectedCheckpoint && (
        <ResumeModal
          checkpoint={selectedCheckpoint}
          isOpen={!!selectedCheckpoint}
          onClose={() => setSelectedCheckpoint(null)}
          onSuccess={() => {
            setSelectedCheckpoint(null);
            if (onRefresh) onRefresh();
          }}
        />
      )}
    </div>
  );
}

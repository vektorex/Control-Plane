"use client";

import React from "react";
import {
  ShieldAlert,
  Database,
  FileCheck2,
  Lock,
  Workflow,
  Layers,
  ArrowRight,
  ExternalLink,
  Shield,
  FileText,
} from "lucide-react";

export function InvestigationGraphViewer({ investigation }) {
  if (!investigation) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        No investigation graph available.
      </div>
    );
  }

  const {
    incident,
    signals = [],
    timeline = [],
    containment_actions = [],
    affected_data_assets = [],
    compliance_evidence = [],
    related_jobs = [],
    related_workflows = [],
  } = investigation;

  return (
    <div className="space-y-6">
      {/* Topology summary banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h4 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-400" />
          Bounded Investigation Graph
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 text-center">
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-xs text-slate-500 block">Signals</span>
            <strong className="text-base text-amber-400 font-bold">{signals.length}</strong>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-xs text-slate-500 block">Data Assets</span>
            <strong className="text-base text-rose-400 font-bold">{affected_data_assets.length}</strong>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-xs text-slate-500 block">Evidence Hashes</span>
            <strong className="text-base text-cyan-400 font-bold">{compliance_evidence.length}</strong>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-xs text-slate-500 block">Containments</span>
            <strong className="text-base text-orange-400 font-bold">{containment_actions.length}</strong>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-xs text-slate-500 block">Related Jobs</span>
            <strong className="text-base text-purple-400 font-bold">{related_jobs.length}</strong>
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-xs text-slate-500 block">Workflows</span>
            <strong className="text-base text-emerald-400 font-bold">{related_workflows.length}</strong>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Correlated Security Signals */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Correlated Security Signals ({signals.length})
            </h4>
          </div>

          {signals.length === 0 ? (
            <p className="text-xs text-slate-500 py-3 text-center">No correlated signals.</p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {signals.map((sig) => (
                <div
                  key={sig.id}
                  className="bg-slate-950 p-2.5 rounded border border-slate-800/80 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-white">
                      {sig.signal_type}
                    </span>
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                      {sig.severity}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 flex items-center justify-between">
                    <span>Source: {sig.source_type}</span>
                    <span className="font-mono text-slate-500">
                      {new Date(sig.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Affected Step 33 Data Assets */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-rose-400" />
              Affected Data Assets & Classifications ({affected_data_assets.length})
            </h4>
          </div>

          {affected_data_assets.length === 0 ? (
            <p className="text-xs text-slate-500 py-3 text-center">
              No restricted/confidential data assets directly mapped to this incident.
            </p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {affected_data_assets.map((asset) => (
                <div
                  key={asset.id}
                  className="bg-slate-950 p-2.5 rounded border border-slate-800/80 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-white">{asset.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                      {asset.classification_tier || "confidential"}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Type: {asset.asset_type} | Resource: {asset.resource_id}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Compliance Evidence Chaining */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-cyan-400" />
              Compliance Evidence Hash Records ({compliance_evidence.length})
            </h4>
          </div>

          {compliance_evidence.length === 0 ? (
            <p className="text-xs text-slate-500 py-3 text-center">
              No Step 33 compliance evidence records attached.
            </p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {compliance_evidence.map((ev) => (
                <div
                  key={ev.id}
                  className="bg-slate-950 p-2.5 rounded border border-slate-800/80 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{ev.title}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                      {ev.evidence_type}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 truncate">
                    Hash: {ev.payload_hash || "sha256"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Containment History */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-orange-400" />
              Containment Actions Taken ({containment_actions.length})
            </h4>
          </div>

          {containment_actions.length === 0 ? (
            <p className="text-xs text-slate-500 py-3 text-center">
              No containment actions executed for this incident.
            </p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {containment_actions.map((act) => (
                <div
                  key={act.id}
                  className="bg-slate-950 p-2.5 rounded border border-slate-800/80 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white font-mono">{act.action_type}</span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {act.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Target: {act.target_type}/{act.target_id}
                  </div>
                  <div className="text-[11px] text-slate-500 italic">
                    &quot;{act.reason}&quot;
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

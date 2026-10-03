"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  GitFork,
  Database,
  ArrowRight,
  Shield,
  Layers,
  Sparkles,
  Cpu,
  Brain,
  FileText,
  Clock,
  ExternalLink,
} from "lucide-react";
import { getClassificationBadge } from "./AssetListTable";

export function LineageGraphViewer({
  rootAssetId,
  lineageData,
  loading = false,
  depth = 3,
  onDepthChange,
  direction = "both",
  onDirectionChange,
}) {
  const [selectedNode, setSelectedNode] = useState(null);

  const nodes = lineageData?.nodes || [];
  const edges = lineageData?.edges || [];

  const getAssetIcon = (assetType) => {
    switch (assetType) {
      case "document":
      case "document_chunk":
        return <FileText className="w-4 h-4 text-emerald-400" />;
      case "task":
      case "run":
        return <Cpu className="w-4 h-4 text-indigo-400" />;
      case "artifact":
        return <Layers className="w-4 h-4 text-amber-400" />;
      case "memory":
        return <Brain className="w-4 h-4 text-purple-400" />;
      case "cache_entry":
        return <Sparkles className="w-4 h-4 text-cyan-400" />;
      default:
        return <Database className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
      {/* Header & Controls */}
      <div className="p-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <GitFork className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">Provenance Lineage Map</h3>
          <span className="text-xs text-slate-500">
            ({nodes.length} nodes, {edges.length} edges)
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Direction:</span>
            <select
              value={direction}
              onChange={(e) => onDirectionChange && onDirectionChange(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="both">Both</option>
              <option value="upstream">Upstream (Sources)</option>
              <option value="downstream">Downstream (Derived)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Max Depth:</span>
            <select
              value={depth}
              onChange={(e) => onDepthChange && onDepthChange(Number(e.target.value))}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="1">1 Hop</option>
              <option value="2">2 Hops</option>
              <option value="3">3 Hops</option>
              <option value="4">4 Hops</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main View Area */}
      <div className="p-6 min-h-[340px] flex flex-col justify-between">
        {loading ? (
          <div className="flex items-center justify-center h-48 text-slate-500 text-sm animate-pulse">
            Traversing cryptographic provenance graph...
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-sm">
            <GitFork className="w-8 h-8 text-slate-600 mb-2 opacity-60" />
            <p>No lineage connections recorded for this asset yet.</p>
            <p className="text-xs text-slate-600 mt-1">
              Lineage is automatically tracked during document ingestion, RAG runs, and artifact generation.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Visual Node Flow */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {nodes.map((node) => {
                const isRoot = node.id === rootAssetId;
                const isSelected = selectedNode?.id === node.id;

                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`cursor-pointer p-3.5 rounded-xl border transition-all ${
                      isRoot
                        ? "bg-indigo-950/30 border-indigo-500/50 shadow-sm shadow-indigo-500/10 ring-1 ring-indigo-500/30"
                        : isSelected
                        ? "bg-slate-800/80 border-slate-600 shadow-md"
                        : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getAssetIcon(node.asset_type)}
                        <div>
                          <div className="text-xs font-medium text-white truncate max-w-[160px]">
                            {node.name}
                          </div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {node.asset_type}
                          </div>
                        </div>
                      </div>
                      <div>{getClassificationBadge(node.data_classification)}</div>
                    </div>

                    {isRoot && (
                      <div className="mt-2 text-[10px] font-semibold tracking-wider text-indigo-400 uppercase">
                        Current Subject
                      </div>
                    )}

                    <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
                      <span className="font-mono text-[10px] text-slate-500 truncate max-w-[120px]">
                        {node.resource_id}
                      </span>
                      <Link
                        href={`/app/data-governance/assets/${node.id}`}
                        className="text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Inspect <ExternalLink className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Edge Relationships List */}
            {edges.length > 0 && (
              <div className="border-t border-slate-800/80 pt-4">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                  Directed Data Flow Edges
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                  {edges.map((e, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs"
                    >
                      <div className="flex items-center gap-2 font-mono text-slate-300">
                        <span className="text-slate-400">
                          {nodes.find((n) => n.id === e.source_asset_id)?.name || e.source_asset_id.slice(0, 8)}
                        </span>
                        <ArrowRight className="w-3 h-3 text-indigo-400 shrink-0" />
                        <span className="text-indigo-300">
                          {nodes.find((n) => n.id === e.target_asset_id)?.name || e.target_asset_id.slice(0, 8)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                          {e.relationship}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {e.transformation_type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/80 text-xs flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-white">{selectedNode.name}</span>
            <span className="text-slate-400 font-mono">ID: {selectedNode.id}</span>
            <span className="text-slate-400">Storage: {selectedNode.storage_location}</span>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="text-slate-500 hover:text-slate-300 underline"
          >
            Close Details
          </button>
        </div>
      )}
    </div>
  );
}

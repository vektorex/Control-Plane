"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  RefreshCw,
  GitMerge,
  Trash2,
  HelpCircle,
} from "lucide-react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export default function ConflictsPage() {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState("active");
  const [resolvingId, setResolvingId] = useState(null);

  const fetchConflicts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await knowledgeGraphService.listConflicts({
        status: filterStatus === "all" ? undefined : filterStatus,
      });
      setConflicts(res || []);
    } catch (err) {
      console.error("Failed to load conflicts:", err);
      setError(err.message || "Failed to load conflicts");
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => {
    fetchConflicts();
  }, [fetchConflicts]);

  const handleResolve = async (conflictId, action) => {
    const note = prompt(`Enter resolution note for '${action}':`, "Resolved via Knowledge Conflicts UI");
    if (note === null) return;

    try {
      setResolvingId(conflictId);
      await knowledgeGraphService.resolveConflict(conflictId, {
        action: action,
        resolution_notes: note,
      });
      fetchConflicts();
    } catch (err) {
      alert(err.message || "Failed to resolve conflict");
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="w-6 h-6 text-rose-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Knowledge Graph Conflicts
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Detect, audit, and resolve contradictory relationships, duplicate entities, or ambiguous references.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/knowledge">
            <Button variant="outline" size="sm" className="text-xs">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Dashboard
            </Button>
          </Link>
          <Button
            size="sm"
            variant="outline"
            onClick={fetchConflicts}
            disabled={loading}
            className="text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {["active", "resolved", "dismissed", "all"].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition ${
              filterStatus === st
                ? "bg-indigo-600 text-white"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Conflicts List */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            Loading conflicts...
          </div>
        ) : conflicts.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs bg-slate-900/40 border border-slate-800 rounded-xl">
            No {filterStatus !== "all" ? filterStatus : ""} conflicts found.
          </div>
        ) : (
          conflicts.map((conflict) => {
            const isActive = conflict.status === "active";
            const details = conflict.details || {};

            return (
              <div
                key={conflict.id}
                className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        conflict.conflict_type === "contradictory_relationship"
                          ? "destructive"
                          : "warning"
                      }
                      className="text-[10px] uppercase font-bold"
                    >
                      {conflict.conflict_type.replace(/_/g, " ")}
                    </Badge>
                    <span className="font-mono text-xs text-slate-400">
                      ID: {conflict.id.substring(0, 8)}...
                    </span>
                    <Badge
                      variant={isActive ? "outline" : "secondary"}
                      className="text-[10px]"
                    >
                      {conflict.status}
                    </Badge>
                  </div>

                  {isActive && (
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7 px-2.5"
                        disabled={resolvingId === conflict.id}
                        onClick={() => handleResolve(conflict.id, "dismiss")}
                      >
                        Dismiss
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7 px-2.5 text-blue-400 border-blue-800/60 hover:bg-blue-950/40"
                        disabled={resolvingId === conflict.id}
                        onClick={() => handleResolve(conflict.id, "merge")}
                      >
                        <GitMerge className="w-3.5 h-3.5 mr-1" /> Merge
                      </Button>
                      <Button
                        size="sm"
                        className="text-xs h-7 px-2.5 bg-emerald-600 hover:bg-emerald-700"
                        disabled={resolvingId === conflict.id}
                        onClick={() => handleResolve(conflict.id, "resolved")}
                      >
                        <CheckCircle className="w-3.5 h-3.5 mr-1" /> Resolve
                      </Button>
                    </div>
                  )}
                </div>

                {/* Details Viewer */}
                <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg text-xs space-y-2">
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Created: {new Date(conflict.created_at).toLocaleString()}</span>
                    {conflict.resolved_at && (
                      <span className="text-emerald-400">
                        Resolved: {new Date(conflict.resolved_at).toLocaleString()}
                      </span>
                    )}
                  </div>

                  {details.message && (
                    <p className="text-slate-200 font-medium">{details.message}</p>
                  )}

                  {details.candidate_names && (
                    <div className="text-slate-300">
                      <span className="text-slate-500 block mb-1">Conflicting Candidates:</span>
                      <div className="flex gap-2">
                        {details.candidate_names.map((name, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]"
                          >
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {conflict.resolution_notes && (
                    <div className="pt-2 border-t border-slate-800 text-slate-400">
                      <strong className="text-slate-300">Resolution Note:</strong>{" "}
                      {conflict.resolution_notes}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

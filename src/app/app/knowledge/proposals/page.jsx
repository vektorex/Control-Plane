"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Clock,
  CheckCircle,
  XCircle,
  ShieldCheck,
  ArrowLeft,
  Boxes,
  GitBranch,
  FileText,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export default function ProposalsReviewPage() {
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState("pending");
  const [actionInProgress, setActionInProgress] = useState(null);

  const fetchProposals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await knowledgeGraphService.listProposals({
        status: filterStatus === "all" ? undefined : filterStatus,
      });
      setProposals(res || []);
    } catch (err) {
      console.error("Failed to fetch proposals:", err);
      setError(err.message || "Failed to load graph change proposals");
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  const handleApprove = async (proposalId) => {
    try {
      setActionInProgress(proposalId);
      await knowledgeGraphService.approveProposal(proposalId, {
        review_note: "Approved by operator via Knowledge Review UI",
      });
      fetchProposals();
    } catch (err) {
      alert(err.message || "Failed to approve proposal");
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (proposalId) => {
    const reason = prompt("Enter reason for rejection (optional):", "Rejected by operator");
    if (reason === null) return;

    try {
      setActionInProgress(proposalId);
      await knowledgeGraphService.rejectProposal(proposalId, {
        review_note: reason,
      });
      fetchProposals();
    } catch (err) {
      alert(err.message || "Failed to reject proposal");
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Graph Change Proposals
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Review and govern model-extracted graph additions before persistence (HITL workflow).
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
            onClick={fetchProposals}
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
        {["pending", "approved", "rejected", "all"].map((st) => (
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

      {/* Proposals List */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            Loading proposals...
          </div>
        ) : proposals.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs bg-slate-900/40 border border-slate-800 rounded-xl">
            No {filterStatus !== "all" ? filterStatus : ""} proposals found.
          </div>
        ) : (
          proposals.map((prop) => {
            const entities = prop.proposed_entities || [];
            const rels = prop.proposed_relationships || [];
            const isPending = prop.status === "pending";

            return (
              <div
                key={prop.id}
                className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-slate-400">
                      ID: {prop.id.substring(0, 8)}...
                    </span>
                    <Badge
                      variant={
                        prop.status === "pending"
                          ? "warning"
                          : prop.status === "approved"
                          ? "success"
                          : "destructive"
                      }
                      className="text-[10px] uppercase font-bold"
                    >
                      {prop.status}
                    </Badge>
                    <span className="text-slate-500 text-xs">
                      Source: {prop.source_id || "unspecified"}
                    </span>
                  </div>

                  {isPending && (
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="destructive"
                        className="text-xs h-7 px-3"
                        disabled={actionInProgress === prop.id}
                        onClick={() => handleReject(prop.id)}
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                      </Button>
                      <Button
                        size="sm"
                        className="text-xs h-7 px-3 bg-emerald-600 hover:bg-emerald-700"
                        disabled={actionInProgress === prop.id}
                        onClick={() => handleApprove(prop.id)}
                      >
                        <CheckCircle className="w-3.5 h-3.5 mr-1" /> Approve
                      </Button>
                    </div>
                  )}
                </div>

                {/* Proposed Entities */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Boxes className="w-3.5 h-3.5 text-indigo-400" />
                    Proposed Entities ({entities.length})
                  </h4>
                  {entities.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                      {entities.map((e, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-slate-200 truncate">
                              {e.canonical_name}
                            </span>
                            <Badge variant="outline" className="text-[9px] uppercase">
                              {e.entity_type}
                            </Badge>
                          </div>
                          {e.description && (
                            <p className="text-[11px] text-slate-400 line-clamp-2">
                              {e.description}
                            </p>
                          )}
                          {e.confidence && (
                            <span className="text-[10px] text-slate-500 block mt-1">
                              Confidence: {Math.round(e.confidence * 100)}%
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-500 text-xs italic">
                      No new entities proposed.
                    </span>
                  )}
                </div>

                {/* Proposed Relationships */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <GitBranch className="w-3.5 h-3.5 text-blue-400" />
                    Proposed Relationships ({rels.length})
                  </h4>
                  {rels.length > 0 ? (
                    <div className="divide-y divide-slate-800/60 border border-slate-800 rounded-lg overflow-hidden text-xs">
                      {rels.map((r, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 bg-slate-950/40 flex items-center justify-between"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-200">
                              {r.source_name}
                            </span>
                            <Badge variant="secondary" className="text-[10px] font-bold">
                              {r.relationship_type.replace(/_/g, " ")}
                            </Badge>
                            <span className="font-medium text-slate-200">
                              {r.target_name}
                            </span>
                          </div>
                          {r.confidence && (
                            <span className="text-[10px] text-slate-400">
                              {Math.round(r.confidence * 100)}%
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-500 text-xs italic">
                      No new relationships proposed.
                    </span>
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

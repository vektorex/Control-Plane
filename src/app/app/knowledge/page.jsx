"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Network,
  Plus,
  Search,
  Sparkles,
  GitBranch,
  ShieldAlert,
  Clock,
  RefreshCw,
  ExternalLink,
  Layers,
  ArrowRight,
  Database,
  FileText,
  Boxes,
  Activity,
} from "lucide-react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EntityModal } from "@/components/features/knowledge/EntityModal";
import { RelationshipModal } from "@/components/features/knowledge/RelationshipModal";
import { ExtractionModal } from "@/components/features/knowledge/ExtractionModal";

export default function KnowledgeDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [entities, setEntities] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [showEntityModal, setShowEntityModal] = useState(false);
  const [showRelModal, setShowRelModal] = useState(false);
  const [showExtractModal, setShowExtractModal] = useState(false);

  const fetchKnowledgeData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Default mock workspace UUID fallback if not set in local storage
      const wsId =
        typeof window !== "undefined"
          ? localStorage.getItem("current_workspace_id") ||
            "00000000-0000-0000-0000-000000000001"
          : "00000000-0000-0000-0000-000000000001";

      const [summaryRes, entitiesRes, relsRes] = await Promise.allSettled([
        knowledgeGraphService.getSummary(wsId),
        knowledgeGraphService.listEntities({ limit: 8 }),
        knowledgeGraphService.listRelationships({ limit: 8 }),
      ]);

      if (summaryRes.status === "fulfilled") {
        setSummary(summaryRes.value);
      }
      if (entitiesRes.status === "fulfilled") {
        setEntities(entitiesRes.value || []);
      }
      if (relsRes.status === "fulfilled") {
        setRelationships(relsRes.value || []);
      }
    } catch (err) {
      console.error("Failed to load knowledge graph data:", err);
      setError(err.message || "Failed to load knowledge data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKnowledgeData();
  }, [fetchKnowledgeData]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Network className="w-6 h-6 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Knowledge Graph
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Relational and structured knowledge layer complementing semantic vector retrieval.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowExtractModal(true)}
            className="text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
            Extract from Text
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowRelModal(true)}
            className="text-xs"
          >
            <GitBranch className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
            Connect
          </Button>

          <Button
            size="sm"
            onClick={() => setShowEntityModal(true)}
            className="text-xs"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            New Entity
          </Button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300 flex items-center justify-between">
          <span>{error}</span>
          <Button size="sm" variant="ghost" onClick={fetchKnowledgeData}>
            Retry
          </Button>
        </div>
      )}

      {/* Metrics Row (Factual Counts - Step 29 Requirement 51) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Entities"
          value={summary?.total_entities ?? entities.length}
          icon={Boxes}
          description="Resolved canonical nodes"
          trend="neutral"
        />
        <StatCard
          title="Relationships"
          value={summary?.total_relationships ?? relationships.length}
          icon={Network}
          description="Typed knowledge edges"
          trend="neutral"
        />
        <StatCard
          title="Pending Proposals"
          value={summary?.pending_proposals ?? 0}
          icon={Clock}
          description="Awaiting HITL review"
          trend={summary?.pending_proposals > 0 ? "warning" : "positive"}
        />
        <StatCard
          title="Active Conflicts"
          value={summary?.active_conflicts ?? 0}
          icon={ShieldAlert}
          description="Contradictions or duplicates"
          trend={summary?.active_conflicts > 0 ? "negative" : "positive"}
        />
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-800 gap-6 text-xs font-medium">
        <Link
          href="/app/knowledge"
          className="pb-2.5 border-b-2 border-indigo-500 text-indigo-400 font-semibold flex items-center gap-1.5"
        >
          <Activity className="w-4 h-4" /> Overview
        </Link>
        <Link
          href="/app/knowledge/graph"
          className="pb-2.5 text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition"
        >
          <Network className="w-4 h-4" /> Visual Graph
        </Link>
        <Link
          href="/app/knowledge/entities"
          className="pb-2.5 text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition"
        >
          <Boxes className="w-4 h-4" /> Entities
        </Link>
        <Link
          href="/app/knowledge/proposals"
          className="pb-2.5 text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition"
        >
          <Clock className="w-4 h-4" /> Proposals
          {summary?.pending_proposals > 0 && (
            <Badge variant="warning" className="text-[10px] ml-1">
              {summary.pending_proposals}
            </Badge>
          )}
        </Link>
        <Link
          href="/app/knowledge/conflicts"
          className="pb-2.5 text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition"
        >
          <ShieldAlert className="w-4 h-4" /> Conflicts
          {summary?.active_conflicts > 0 && (
            <Badge variant="destructive" className="text-[10px] ml-1">
              {summary.active_conflicts}
            </Badge>
          )}
        </Link>
      </div>

      {/* Entity Breakdown by Type */}
      {summary?.entity_types && Object.keys(summary.entity_types).length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Entities by Type
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.entity_types).map(([type, count]) => (
              <Link
                key={type}
                href={`/app/knowledge/entities?type=${type}`}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/70 border border-slate-700/60 hover:border-slate-600 text-xs transition"
              >
                <span className="capitalize text-slate-300">{type}</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-700/80 text-[10px] font-mono text-slate-400 font-bold">
                  {count}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Two Column Grid: Recent Entities & Recent Relationships */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Entities Column */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Boxes className="w-4 h-4 text-indigo-400" />
                Recent Entities
              </h3>
              <Link
                href="/app/knowledge/entities"
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                Loading entities...
              </div>
            ) : entities.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No entities found. Create an entity or run extraction.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60">
                {entities.map((ent) => (
                  <div
                    key={ent.id}
                    className="py-2.5 flex items-center justify-between hover:bg-slate-800/30 px-2 rounded-lg transition"
                  >
                    <div className="min-w-0 pr-3">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/app/knowledge/entities/${ent.id}`}
                          className="font-medium text-xs text-slate-200 hover:text-indigo-400 truncate block"
                        >
                          {ent.canonical_name}
                        </Link>
                        <Badge variant="outline" className="text-[10px] uppercase">
                          {ent.entity_type}
                        </Badge>
                      </div>
                      {ent.description && (
                        <p className="text-[11px] text-slate-400 truncate mt-0.5 max-w-sm">
                          {ent.description}
                        </p>
                      )}
                    </div>
                    <Link
                      href={`/app/knowledge/entities/${ent.id}`}
                      className="text-slate-500 hover:text-slate-300 p-1"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Relationships Column */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Network className="w-4 h-4 text-blue-400" />
                Recent Relationships
              </h3>
              <Link
                href="/app/knowledge/graph"
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                Explore Graph <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                Loading relationships...
              </div>
            ) : relationships.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No relationships recorded yet.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60">
                {relationships.map((rel) => (
                  <div
                    key={rel.id}
                    className="py-2.5 flex items-center justify-between hover:bg-slate-800/30 px-2 rounded-lg transition"
                  >
                    <div className="min-w-0 pr-3 flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-300 truncate max-w-[120px]">
                        {rel.source_entity_id?.substring(0, 8)}...
                      </span>
                      <Badge variant="secondary" className="text-[10px] font-bold">
                        {rel.relationship_type.replace(/_/g, " ")}
                      </Badge>
                      <span className="font-mono text-xs text-slate-300 truncate max-w-[120px]">
                        {rel.target_entity_id?.substring(0, 8)}...
                      </span>
                    </div>
                    {rel.confidence && (
                      <span className="text-[10px] text-slate-400">
                        {Math.round(rel.confidence * 100)}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <EntityModal
        isOpen={showEntityModal}
        onClose={() => setShowEntityModal(false)}
        onSuccess={fetchKnowledgeData}
      />
      <RelationshipModal
        isOpen={showRelModal}
        onClose={() => setShowRelModal(false)}
        onSuccess={fetchKnowledgeData}
        entities={entities}
      />
      <ExtractionModal
        isOpen={showExtractModal}
        onClose={() => setShowExtractModal(false)}
        onSuccess={fetchKnowledgeData}
      />
    </div>
  );
}

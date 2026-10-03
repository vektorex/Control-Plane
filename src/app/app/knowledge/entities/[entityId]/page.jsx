"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Boxes,
  ArrowLeft,
  Tag,
  GitBranch,
  FileCode,
  Shield,
  Layers,
  Clock,
  Archive,
  RefreshCw,
  ExternalLink,
  Plus,
} from "lucide-react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { RelationshipModal } from "@/components/features/knowledge/RelationshipModal";

export default function EntityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const entityId = params?.entityId;

  const [entity, setEntity] = useState(null);
  const [neighbors, setNeighbors] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [archiving, setArchiving] = useState(false);

  const fetchEntityDetails = useCallback(async () => {
    if (!entityId) return;
    try {
      setLoading(true);
      setError(null);
      const [entRes, neighborsRes] = await Promise.all([
        knowledgeGraphService.getEntity(entityId),
        knowledgeGraphService.getNeighbors(entityId),
      ]);
      setEntity(entRes);
      setNeighbors(neighborsRes);
    } catch (err) {
      console.error("Failed to load entity detail:", err);
      setError(err.message || "Failed to load entity details");
    } finally {
      setLoading(false);
    }
  }, [entityId]);

  useEffect(() => {
    fetchEntityDetails();
  }, [fetchEntityDetails]);

  const handleArchive = async () => {
    if (!confirm("Are you sure you want to archive this entity? Relationships will also be archived.")) {
      return;
    }
    try {
      setArchiving(true);
      await knowledgeGraphService.archiveEntity(entityId);
      router.push("/app/knowledge/entities");
    } catch (err) {
      alert(err.message || "Failed to archive entity");
      setArchiving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-500 text-xs">
        Loading entity details...
      </div>
    );
  }

  if (error || !entity) {
    return (
      <div className="space-y-4">
        <Link
          href="/app/knowledge/entities"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Entities
        </Link>
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300">
          {error || "Entity not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div className="space-y-1">
          <Link
            href="/app/knowledge/entities"
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 mb-2 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Entities
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              {entity.canonical_name}
            </h1>
            <Badge variant="outline" className="text-xs uppercase font-bold">
              {entity.entity_type}
            </Badge>
            <Badge
              variant={entity.status === "active" ? "secondary" : "outline"}
              className="text-xs"
            >
              {entity.status}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConnectModal(true)}
            className="text-xs"
          >
            <GitBranch className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
            Connect Entity
          </Button>

          <Button
            variant="destructive"
            size="sm"
            onClick={handleArchive}
            disabled={archiving}
            className="text-xs"
          >
            <Archive className="w-3.5 h-3.5 mr-1.5" />
            {archiving ? "Archiving..." : "Archive"}
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <span className="text-slate-500 block mb-1">Entity ID</span>
          <span className="font-mono text-slate-300 select-all block truncate">
            {entity.id}
          </span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <span className="text-slate-500 block mb-1">Grounding Confidence</span>
          <span className="font-medium text-slate-200">
            {entity.confidence ? `${Math.round(entity.confidence * 100)}%` : "Verified / Explicit"}
          </span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <span className="text-slate-500 block mb-1">Sources Grounded</span>
          <span className="font-medium text-slate-200">
            {entity.source_count || 1} independent source(s)
          </span>
        </div>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <span className="text-slate-500 block mb-1">Connected Edges</span>
          <span className="font-medium text-slate-200">
            {(neighbors?.outgoing_relationships?.length || 0) +
              (neighbors?.incoming_relationships?.length || 0)}{" "}
            relationship(s)
          </span>
        </div>
      </div>

      {/* Description */}
      {entity.description && (
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Description
          </h3>
          <p className="text-slate-200 text-sm leading-relaxed">
            {entity.description}
          </p>
        </div>
      )}

      {/* Aliases & Properties Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Aliases */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-indigo-400" />
            Aliases & Recognized Variations
          </h3>
          {entity.aliases && entity.aliases.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {entity.aliases.map((al, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 font-mono text-xs"
                >
                  {al}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-xs">No aliases registered.</p>
          )}
        </div>

        {/* Properties JSON */}
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <FileCode className="w-3.5 h-3.5 text-blue-400" />
            Extracted Properties
          </h3>
          {entity.properties && Object.keys(entity.properties).length > 0 ? (
            <pre className="p-3 bg-slate-950 rounded-lg text-slate-300 text-[11px] font-mono overflow-auto max-h-40">
              {JSON.stringify(entity.properties, null, 2)}
            </pre>
          ) : (
            <p className="text-slate-500 text-xs">No custom properties.</p>
          )}
        </div>
      </div>

      {/* Connected Relationships Section */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-indigo-400" />
          1-Hop Knowledge Relationships
        </h3>

        <div className="space-y-3">
          {/* Outgoing */}
          {neighbors?.outgoing_relationships &&
            neighbors.outgoing_relationships.length > 0 && (
              <div>
                <span className="text-[11px] text-slate-500 uppercase font-semibold mb-2 block">
                  Outgoing Connections ({entity.canonical_name} → Target)
                </span>
                <div className="divide-y divide-slate-800/60 border border-slate-800/80 rounded-lg overflow-hidden">
                  {neighbors.outgoing_relationships.map((rel) => (
                    <div
                      key={rel.id}
                      className="p-3 bg-slate-900/40 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">{entity.canonical_name}</span>
                        <Badge variant="secondary" className="text-[10px] font-bold">
                          {rel.relationship_type.replace(/_/g, " ")}
                        </Badge>
                        <Link
                          href={`/app/knowledge/entities/${rel.target_entity_id}`}
                          className="font-medium text-indigo-400 hover:underline"
                        >
                          Target ({rel.target_entity_id?.substring(0, 8)}...)
                        </Link>
                      </div>
                      {rel.confidence && (
                        <span className="text-slate-500 text-[10px]">
                          {Math.round(rel.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Incoming */}
          {neighbors?.incoming_relationships &&
            neighbors.incoming_relationships.length > 0 && (
              <div className="mt-4">
                <span className="text-[11px] text-slate-500 uppercase font-semibold mb-2 block">
                  Incoming Connections (Source → {entity.canonical_name})
                </span>
                <div className="divide-y divide-slate-800/60 border border-slate-800/80 rounded-lg overflow-hidden">
                  {neighbors.incoming_relationships.map((rel) => (
                    <div
                      key={rel.id}
                      className="p-3 bg-slate-900/40 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/app/knowledge/entities/${rel.source_entity_id}`}
                          className="font-medium text-indigo-400 hover:underline"
                        >
                          Source ({rel.source_entity_id?.substring(0, 8)}...)
                        </Link>
                        <Badge variant="secondary" className="text-[10px] font-bold">
                          {rel.relationship_type.replace(/_/g, " ")}
                        </Badge>
                        <span className="text-slate-400">{entity.canonical_name}</span>
                      </div>
                      {rel.confidence && (
                        <span className="text-slate-500 text-[10px]">
                          {Math.round(rel.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {(!neighbors?.outgoing_relationships ||
            neighbors.outgoing_relationships.length === 0) &&
            (!neighbors?.incoming_relationships ||
              neighbors.incoming_relationships.length === 0) && (
              <p className="text-slate-500 text-xs py-4 text-center">
                No connected relationships. Use "Connect Entity" above to link to other entities.
              </p>
            )}
        </div>
      </div>

      {/* Connect Modal */}
      <RelationshipModal
        isOpen={showConnectModal}
        onClose={() => setShowConnectModal(false)}
        onSuccess={fetchEntityDetails}
        defaultSourceId={entity.id}
        entities={neighbors?.connected_entities || [entity]}
      />
    </div>
  );
}

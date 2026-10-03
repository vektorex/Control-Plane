"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Boxes,
  Plus,
  Search,
  Filter,
  ExternalLink,
  GitMerge,
  ArrowUpDown,
  Tag,
  ShieldCheck,
  Archive,
} from "lucide-react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EntityModal } from "@/components/features/knowledge/EntityModal";

export default function EntitiesExplorerPage() {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("active");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMergeModal, setShowMergeModal] = useState(false);
  const [primaryMergeId, setPrimaryMergeId] = useState("");
  const [duplicateMergeId, setDuplicateMergeId] = useState("");
  const [mergeReason, setMergeReason] = useState("");
  const [merging, setMerging] = useState(false);

  const fetchEntities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      let res;
      if (searchQuery.trim()) {
        res = await knowledgeGraphService.searchEntities({
          name: searchQuery.trim(),
          ...(selectedType !== "all" ? { entity_type: selectedType } : {}),
        });
      } else {
        res = await knowledgeGraphService.listEntities({
          status: selectedStatus,
          ...(selectedType !== "all" ? { entity_type: selectedType } : {}),
          limit: 50,
        });
      }
      setEntities(res || []);
    } catch (err) {
      console.error("Failed to load entities:", err);
      setError(err.message || "Failed to load entities");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedType, selectedStatus]);

  useEffect(() => {
    fetchEntities();
  }, [fetchEntities]);

  const handleMerge = async (e) => {
    e.preventDefault();
    if (!primaryMergeId || !duplicateMergeId) return;
    if (primaryMergeId === duplicateMergeId) {
      alert("Cannot merge an entity into itself.");
      return;
    }
    try {
      setMerging(true);
      await knowledgeGraphService.mergeEntities({
        primary_entity_id: primaryMergeId,
        duplicate_entity_id: duplicateMergeId,
        merge_reason: mergeReason || "Operator resolution",
      });
      setShowMergeModal(false);
      setPrimaryMergeId("");
      setDuplicateMergeId("");
      setMergeReason("");
      fetchEntities();
    } catch (err) {
      alert(err.message || "Merge operation failed");
    } finally {
      setMerging(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Boxes className="w-6 h-6 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Entities Explorer
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Canonical knowledge graph entities, aliases, and source grounding.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowMergeModal(true)}
            className="text-xs"
          >
            <GitMerge className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
            Merge Entities
          </Button>
          <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="text-xs"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            New Entity
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by canonical name or alias..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-800/80 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs bg-slate-800/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Types</option>
            <option value="technology">Technology</option>
            <option value="service">Service</option>
            <option value="api">API</option>
            <option value="database">Database</option>
            <option value="model">Model</option>
            <option value="prompt">Prompt</option>
            <option value="document">Document</option>
            <option value="repository">Repository</option>
            <option value="person">Person</option>
            <option value="organization">Organization</option>
            <option value="workflow">Workflow</option>
            <option value="issue">Issue</option>
            <option value="pull_request">Pull Request</option>
            <option value="concept">Concept</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs bg-slate-800/80 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Entities Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            Loading entities...
          </div>
        ) : entities.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            No entities found matching your filters.
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/30 text-slate-400 uppercase text-[10px] font-semibold">
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Sources</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {entities.map((entity) => (
                <tr
                  key={entity.id}
                  className="hover:bg-slate-800/40 transition-colors"
                >
                  <td className="py-3 px-4">
                    <Link
                      href={`/app/knowledge/entities/${entity.id}`}
                      className="font-medium text-slate-100 hover:text-indigo-400 block"
                    >
                      {entity.canonical_name}
                    </Link>
                    {entity.description && (
                      <span className="text-[11px] text-slate-500 truncate block max-w-md">
                        {entity.description}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <Badge variant="outline" className="text-[10px] uppercase">
                      {entity.entity_type}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400">
                    {entity.source_count || 1}
                  </td>
                  <td className="py-3 px-4">
                    {entity.confidence ? (
                      <span className="text-slate-300 font-medium">
                        {Math.round(entity.confidence * 100)}%
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <Badge
                      variant={entity.status === "active" ? "secondary" : "outline"}
                      className="text-[10px]"
                    >
                      {entity.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      href={`/app/knowledge/entities/${entity.id}`}
                      className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 text-xs p-1"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Merge Modal */}
      {showMergeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-lg font-semibold text-slate-100 mb-1">
              Merge Entities
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Safely transfer relationships and aliases from duplicate to canonical entity. Duplicate will be archived.
            </p>

            <form onSubmit={handleMerge} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Primary / Canonical Entity *
                </label>
                <select
                  required
                  value={primaryMergeId}
                  onChange={(e) => setPrimaryMergeId(e.target.value)}
                  className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">Select canonical entity...</option>
                  {entities.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.canonical_name} ({e.entity_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Duplicate Entity to Merge *
                </label>
                <select
                  required
                  value={duplicateMergeId}
                  onChange={(e) => setDuplicateMergeId(e.target.value)}
                  className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">Select duplicate entity...</option>
                  {entities.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.canonical_name} ({e.entity_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">
                  Merge Justification / Audit Reason
                </label>
                <input
                  type="text"
                  value={mergeReason}
                  onChange={(e) => setMergeReason(e.target.value)}
                  placeholder="e.g. Duplicate naming detected during reconciliation"
                  className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowMergeModal(false)}
                  disabled={merging}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={merging}>
                  {merging ? "Merging..." : "Confirm Safe Merge"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Entity Modal */}
      <EntityModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={fetchEntities}
      />
    </div>
  );
}

"use client";

import React, { useState } from "react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Button } from "@/components/ui/Button";

const ALLOWED_RELATIONSHIP_TYPES = [
  "owns",
  "member_of",
  "part_of",
  "depends_on",
  "uses",
  "implements",
  "calls",
  "imports",
  "contains",
  "references",
  "related_to",
  "derived_from",
  "created_by",
  "assigned_to",
  "belongs_to",
  "deployed_to",
  "configured_by",
  "documents",
  "mentions",
  "blocks",
  "duplicates",
  "supersedes",
  "tested_by",
  "evaluated_by",
];

export function RelationshipModal({
  isOpen,
  onClose,
  onSuccess,
  entities = [],
  defaultSourceId = null,
  projectId = null,
}) {
  const [sourceEntityId, setSourceEntityId] = useState(defaultSourceId || "");
  const [targetEntityId, setTargetEntityId] = useState("");
  const [relationshipType, setRelationshipType] = useState("depends_on");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!sourceEntityId || !targetEntityId) {
      setError("Both source and target entities are required.");
      return;
    }
    if (sourceEntityId === targetEntityId) {
      setError("Self-relationships are prohibited by graph policy.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const payload = {
        source_entity_id: sourceEntityId,
        relationship_type: relationshipType,
        target_entity_id: targetEntityId,
        properties: {},
        source_reference: { provenance: "manual_ui" },
        project_id: projectId || null,
      };

      const res = await knowledgeGraphService.createRelationship(payload);
      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create relationship");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl">
        <h3 className="text-lg font-semibold text-slate-100 mb-1">
          Add Knowledge Relationship
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Connect two entities in the knowledge graph.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Source Entity *
            </label>
            <select
              required
              value={sourceEntityId}
              onChange={(e) => setSourceEntityId(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Select source entity...</option>
              {entities.map((ent) => (
                <option key={ent.id} value={ent.id}>
                  {ent.canonical_name} ({ent.entity_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Relationship Type *
            </label>
            <select
              value={relationshipType}
              onChange={(e) => setRelationshipType(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {ALLOWED_RELATIONSHIP_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Target Entity *
            </label>
            <select
              required
              value={targetEntityId}
              onChange={(e) => setTargetEntityId(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Select target entity...</option>
              {entities.map((ent) => (
                <option key={ent.id} value={ent.id}>
                  {ent.canonical_name} ({ent.entity_type})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Connecting..." : "Connect Entities"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

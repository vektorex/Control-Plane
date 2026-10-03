"use client";

import React, { useState } from "react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Button } from "@/components/ui/Button";

const ALLOWED_ENTITY_TYPES = [
  "technology",
  "service",
  "api",
  "database",
  "model",
  "prompt",
  "document",
  "file",
  "repository",
  "person",
  "organization",
  "project",
  "task",
  "workflow",
  "workflow_step",
  "issue",
  "pull_request",
  "concept",
  "topic",
  "dataset",
  "event",
];

export function EntityModal({ isOpen, onClose, onSuccess, workspaceId, projectId }) {
  const [canonicalName, setCanonicalName] = useState("");
  const [entityType, setEntityType] = useState("technology");
  const [description, setDescription] = useState("");
  const [aliases, setAliases] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canonicalName.trim()) {
      setError("Canonical name is required.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const aliasList = aliases
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean);

      const payload = {
        canonical_name: canonicalName.trim(),
        entity_type: entityType,
        description: description.trim() || null,
        aliases: aliasList,
        properties: {},
        project_id: projectId || null,
      };

      const res = await knowledgeGraphService.createEntity(payload);
      if (onSuccess) onSuccess(res);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create entity");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl">
        <h3 className="text-lg font-semibold text-slate-100 mb-1">
          Create Knowledge Entity
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Add a trusted entity to the relational knowledge graph.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Canonical Name *
            </label>
            <input
              type="text"
              required
              value={canonicalName}
              onChange={(e) => setCanonicalName(e.target.value)}
              placeholder="e.g. Authentication Service or PostgreSQL"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Entity Type *
            </label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {ALLOWED_ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Description
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the entity and its role"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Aliases (comma separated)
            </label>
            <input
              type="text"
              value={aliases}
              onChange={(e) => setAliases(e.target.value)}
              placeholder="e.g. AuthSvc, auth-api, OAuth Provider"
              className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
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
              {submitting ? "Creating..." : "Create Entity"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

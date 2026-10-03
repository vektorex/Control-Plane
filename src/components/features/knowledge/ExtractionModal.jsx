"use client";

import React, { useState } from "react";
import { knowledgeGraphService } from "@/services/knowledgeGraph";
import { Button } from "@/components/ui/Button";

export function ExtractionModal({
  isOpen,
  onClose,
  onSuccess,
  workspaceId,
  projectId = null,
}) {
  const [text, setText] = useState("");
  const [sourceType, setSourceType] = useState("document");
  const [requireApproval, setRequireApproval] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) {
      setError("Text content is required for extraction.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setResult(null);

      const payload = {
        text: text.trim(),
        source_type: sourceType,
        source_id: `manual_input_${Date.now()}`,
        workspace_id: workspaceId,
        project_id: projectId || null,
        require_approval: requireApproval,
      };

      const res = await knowledgeGraphService.extractGraph(payload);
      setResult(res);
      if (onSuccess) onSuccess(res);
    } catch (err) {
      setError(err.message || "Extraction failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 shadow-2xl">
        <h3 className="text-lg font-semibold text-slate-100 mb-1">
          Extract Knowledge Graph
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Parse text using the AI Gateway to extract structured entities and relationships.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300">
            {error}
          </div>
        )}

        {result ? (
          <div className="space-y-4">
            <div className="p-4 bg-emerald-950/30 border border-emerald-800/50 rounded-lg text-xs text-emerald-300">
              <h4 className="font-semibold text-emerald-200 mb-1">
                Extraction Complete!
              </h4>
              <p>{result.message}</p>
              <div className="mt-2 flex gap-4 text-xs font-mono">
                <span>Entities: {result.entities_created}</span>
                <span>Relationships: {result.relationships_created}</span>
                {result.proposal_id && (
                  <span className="text-indigo-400">
                    Proposal Created (Awaiting Review)
                  </span>
                )}
              </div>
            </div>

            <div className="flex justify-end">
              <Button size="sm" onClick={onClose}>
                Done
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Source Type
              </label>
              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="document">Document / Specification</option>
                <option value="workflow">Workflow Execution</option>
                <option value="task">Task Directives</option>
                <option value="connector">Connector Payload</option>
                <option value="manual">Manual Input</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Content to Analyze *
              </label>
              <textarea
                required
                rows={6}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste architectural text, technical documentation, or API descriptions here..."
                className="w-full bg-slate-800/90 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono text-[11px]"
              />
            </div>

            <div className="flex items-center gap-2 p-2 bg-slate-800/50 border border-slate-700/60 rounded-lg">
              <input
                type="checkbox"
                id="requireApproval"
                checked={requireApproval}
                onChange={(e) => setRequireApproval(e.target.checked)}
                className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="requireApproval" className="text-slate-300 text-xs cursor-pointer">
                Require human review before persisting (Create Graph Change Proposal)
              </label>
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
                {submitting ? "Extracting..." : "Run Extraction"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

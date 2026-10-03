"use client";

import React, { useState } from "react";
import { Bookmark, Highlighter, HelpCircle, AlertTriangle, ShieldCheck, Plus } from "lucide-react";

export function AnnotationOverlay({
  annotations = [],
  currentUserId,
  onCreateAnnotation,
}) {
  const [content, setContent] = useState("");
  const [annotationType, setAnnotationType] = useState("highlight");
  const [targetKey, setTargetKey] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!content.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onCreateAnnotation({
        annotation_type: annotationType,
        target: { element: targetKey || "general" },
        content,
      });
      setContent("");
      setTargetKey("");
      setIsAdding(false);
    } finally {
      setSubmitting(false);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case "highlight":
        return <Highlighter className="w-3 h-3 text-amber-400" />;
      case "question":
        return <HelpCircle className="w-3 h-3 text-blue-400" />;
      case "warning":
        return <AlertTriangle className="w-3 h-3 text-rose-400" />;
      case "decision":
        return <ShieldCheck className="w-3 h-3 text-emerald-400" />;
      default:
        return <Bookmark className="w-3 h-3 text-indigo-400" />;
    }
  };

  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bookmark className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-semibold text-slate-200">Annotations & Evidence ({annotations.length})</h4>
        </div>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
        >
          {isAdding ? "Cancel" : "+ Annotate"}
        </button>
      </div>

      {isAdding && (
        <form onSubmit={handleCreate} className="flex flex-col gap-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800">
          <div className="flex items-center gap-2">
            <select
              value={annotationType}
              onChange={(e) => setAnnotationType(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
            >
              <option value="highlight">Highlight</option>
              <option value="question">Question</option>
              <option value="warning">Warning</option>
              <option value="evidence">Evidence</option>
              <option value="decision">Decision</option>
            </select>
            <input
              type="text"
              value={targetKey}
              onChange={(e) => setTargetKey(e.target.value)}
              placeholder="Target section / node..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 placeholder-slate-600 focus:outline-none"
            />
          </div>
          <input
            type="text"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Annotation note or finding..."
            className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 placeholder-slate-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={submitting || !content.trim()}
            className="self-end px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded text-xs font-medium"
          >
            Save Annotation
          </button>
        </form>
      )}

      <div className="flex flex-col gap-2 max-h-[200px] overflow-y-auto">
        {annotations.length === 0 ? (
          <div className="text-center py-4 text-slate-500 text-xs">No annotations yet.</div>
        ) : (
          annotations.map((ann) => (
            <div
              key={ann.id}
              className="flex flex-col gap-1 p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs"
            >
              <div className="flex items-center justify-between text-[10px] text-slate-500">
                <span className="flex items-center gap-1 font-semibold uppercase text-slate-300">
                  {getIcon(ann.annotation_type)}
                  {ann.annotation_type}
                </span>
                <span>{ann.target?.element || "General"}</span>
              </div>
              <p className="text-slate-300 leading-snug">{ann.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

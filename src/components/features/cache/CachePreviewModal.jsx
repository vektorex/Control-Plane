"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Search, Sparkles, CheckCircle2, XCircle, AlertCircle, ArrowRight } from "lucide-react";
import { cacheService } from "@/services/cache";

export function CachePreviewModal({ isOpen, onClose, workspaceId }) {
  const [promptText, setPromptText] = useState("");
  const [taskType, setTaskType] = useState("summarization");
  const [modelId, setModelId] = useState("gpt-4o-mini");
  const [probing, setProbing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleProbe = async (e) => {
    e.preventDefault();
    if (!promptText.trim()) return;
    setError(null);
    setProbing(true);

    try {
      const res = await cacheService.preview({
        prompt_text: promptText.trim(),
        task_type: taskType.trim() || null,
        model_id: modelId.trim() || null,
        workspace_id: workspaceId,
      });
      setResult(res);
    } catch (err) {
      setError(err?.message || "Cache preview probe failed");
    } finally {
      setProbing(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        setResult(null);
        setError(null);
        onClose();
      }}
      title="Dry-Run Cache Preview Probe"
    >
      <form onSubmit={handleProbe} className="space-y-4 py-2">
        <p className="text-xs text-muted-foreground">
          Simulate cache lookup behavior for a given task specification without executing any LLM calls
          or modifying workspace cache state.
        </p>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1.5">
            Prompt / Task Text
          </label>
          <textarea
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="Enter the exact or semantic task prompt to test..."
            rows={3}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Task Type Classification
            </label>
            <Input
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              placeholder="e.g. summarization, extraction"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Model Identifier
            </label>
            <Input
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="e.g. gpt-4o-mini"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button type="submit" variant="default" disabled={probing || !promptText.trim()}>
            <Search className="h-4 w-4 mr-1.5" />
            {probing ? "Probing..." : "Test Cache Lookup"}
          </Button>
        </div>
      </form>

      {result && (
        <div className="mt-4 pt-4 border-t border-border/50 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Probe Diagnostics
            </span>
            <Badge variant={result.eligible ? "success" : "destructive"}>
              {result.eligible ? "Eligible for Cache" : "Ineligible for Cache"}
            </Badge>
          </div>

          <div className="rounded-lg border border-border/60 bg-muted/30 p-3.5 space-y-2.5 text-xs">
            <div className="flex items-start justify-between">
              <span className="text-muted-foreground">Eligibility Reason:</span>
              <span className="font-medium text-right text-foreground">{result.reason}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Exact Match Available:</span>
              <span className="flex items-center gap-1 font-medium">
                {result.exact_match_available ? (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    <span className="text-emerald-500">Yes</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>No</span>
                  </>
                )}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Semantic Match Available:</span>
              <span className="flex items-center gap-1 font-medium">
                {result.semantic_candidate_available ? (
                  <>
                    <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
                    <span className="text-indigo-500">
                      Yes ({Math.round((result.candidate_similarity || 0) * 100)}% sim)
                    </span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>No</span>
                  </>
                )}
              </span>
            </div>

            {result.freshness && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Candidate Freshness:</span>
                <span className="font-medium text-emerald-500">{result.freshness}</span>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-primary mb-1">
              <ArrowRight className="h-3.5 w-3.5" />
              <span>Expected System Execution Behavior</span>
            </div>
            <p className="text-muted-foreground">{result.expected_behavior}</p>
          </div>
        </div>
      )}
    </Modal>
  );
}

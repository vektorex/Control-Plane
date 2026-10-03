"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { AlertCircle, Trash2, CheckCircle2 } from "lucide-react";
import { cacheService } from "@/services/cache";

export function CacheInvalidateModal({ isOpen, onClose, workspaceId, onInvalidated }) {
  const [mode, setMode] = useState("namespace");
  const [targetId, setTargetId] = useState("workspace");
  const [reason, setReason] = useState("manual_administrative_invalidation");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successResult, setSuccessResult] = useState(null);

  const modeOptions = [
    { value: "namespace", label: "Namespace (workspace / project / user / global)" },
    { value: "entry", label: "Specific Entry ID" },
    { value: "prompt", label: "Prompt Version ID" },
    { value: "artifact", label: "Multimodal Artifact Hash" },
    { value: "graph", label: "Knowledge Graph Snapshot Hash" },
    { value: "memory", label: "Memory Snapshot Hash" },
    { value: "model", label: "Model ID" },
    { value: "workspace", label: "Entire Workspace" },
  ];

  const handleModeChange = (newMode) => {
    setMode(newMode);
    if (newMode === "namespace") {
      setTargetId("workspace");
    } else if (newMode === "workspace") {
      setTargetId("");
    } else {
      setTargetId("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessResult(null);
    setSubmitting(true);

    try {
      const res = await cacheService.invalidate({
        workspace_id: workspaceId,
        mode: mode,
        target_id: targetId.trim() || null,
        reason: reason.trim() || "manual_invalidation",
      });
      setSuccessResult(res);
      if (onInvalidated) {
        onInvalidated(res);
      }
    } catch (err) {
      setError(err?.message || "Failed to invalidate cache");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        setSuccessResult(null);
        setError(null);
        onClose();
      }}
      title="Surgical Cache Invalidation"
    >
      {successResult ? (
        <div className="space-y-4 py-3">
          <div className="flex items-center gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-emerald-500">
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <div>
              <p className="text-sm font-semibold">Invalidation Complete</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Successfully invalidated <strong>{successResult.invalidated_count}</strong> cache entries
                matching mode <code>{successResult.mode}</code>.
              </p>
            </div>
          </div>
          <div className="flex justify-end">
            <Button
              variant="default"
              onClick={() => {
                setSuccessResult(null);
                onClose();
              }}
            >
              Done
            </Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Invalidation Scope Mode
            </label>
            <Select
              value={mode}
              onChange={(e) => handleModeChange(e.target.value)}
              options={modeOptions}
            />
          </div>

          {mode !== "workspace" && (
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                {mode === "namespace"
                  ? "Namespace Name (e.g. workspace, project, user, global)"
                  : mode === "entry"
                  ? "Cache Entry UUID"
                  : mode === "prompt"
                  ? "Prompt Version UUID"
                  : "Target ID or Content Hash"}
              </label>
              <Input
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                placeholder={mode === "namespace" ? "workspace" : "Paste UUID or hash..."}
                required={mode !== "workspace"}
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Audit Reason
            </label>
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Prompt update, document modified, manual sweep"
            />
          </div>

          <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-500">
            <p className="font-medium">Surgical Scoping Guarantee</p>
            <p className="text-muted-foreground mt-0.5">
              Only entries matching the exact scope above will be invalidated. Other workspace and
              project caches will remain intact.
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" variant="destructive" disabled={submitting}>
              <Trash2 className="h-4 w-4 mr-1.5" />
              {submitting ? "Invalidating..." : "Execute Invalidation"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

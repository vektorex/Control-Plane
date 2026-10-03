"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { AlertCircle, AlertTriangle, Save, CheckCircle2 } from "lucide-react";
import { cacheService } from "@/services/cache";

export function CachePolicyForm({ initialPolicy, workspaceId, onSaved }) {
  const [policy, setPolicy] = useState(initialPolicy || {
    enabled: true,
    default_mode: "auto",
    semantic_enabled: true,
    semantic_threshold: 0.88,
    default_ttl: 86400,
    max_entry_size: 500000,
    allow_cross_model_cache: false,
    stale_while_revalidate: true,
    max_namespace_entries: 10000,
  });

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (field, value) => {
    setPolicy((prev) => ({ ...prev, [field]: value }));
    setSuccess(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const saved = await cacheService.updatePolicy(workspaceId, policy);
      setPolicy(saved);
      setSuccess(true);
      if (onSaved) {
        onSaved(saved);
      }
    } catch (err) {
      setError(err?.message || "Failed to update cache policy");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-500">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Cache policy successfully updated and active for workspace.</span>
        </div>
      )}

      {/* Master Enable & Mode */}
      <div className="rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Global Workspace Controls</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-foreground">Enable Cache Layer</p>
            <p className="text-[11px] text-muted-foreground">
              Master kill-switch for exact and semantic cache lookups and admissions in this workspace.
            </p>
          </div>
          <input
            type="checkbox"
            checked={policy.enabled}
            onChange={(e) => handleChange("enabled", e.target.checked)}
            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1.5">
            Default Execution Cache Mode
          </label>
          <Select
            value={policy.default_mode}
            onChange={(e) => handleChange("default_mode", e.target.value)}
            options={[
              { value: "auto", label: "Auto (Intelligent eligibility analysis)" },
              { value: "enabled", label: "Enabled (Always attempt cache where eligible)" },
              { value: "disabled", label: "Disabled (Always bypass cache)" },
              { value: "refresh", label: "Refresh (Bypass lookup, compute and re-admit)" },
            ]}
          />
        </div>
      </div>

      {/* Semantic Matching Settings */}
      <div className="rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Semantic Matching & Cosine Thresholds</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-foreground">Semantic Similarity Matching</p>
            <p className="text-[11px] text-muted-foreground">
              Fall back to vector similarity lookup when exact fingerprint misses.
            </p>
          </div>
          <input
            type="checkbox"
            checked={policy.semantic_enabled}
            onChange={(e) => handleChange("semantic_enabled", e.target.checked)}
            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
          />
        </div>

        {policy.semantic_enabled && (
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-medium text-muted-foreground">
                Cosine Similarity Threshold Cutoff:{" "}
                <strong className="text-foreground">{policy.semantic_threshold}</strong>
              </label>
              <span className="text-[11px] text-muted-foreground">Range: 0.70 – 0.99</span>
            </div>
            <input
              type="range"
              min="0.70"
              max="0.99"
              step="0.01"
              value={policy.semantic_threshold}
              onChange={(e) => handleChange("semantic_threshold", parseFloat(e.target.value))}
              className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
            />
            {policy.semantic_threshold < 0.85 && (
              <div className="mt-2 flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-2.5 text-xs text-amber-500">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>
                  Threshold below 0.85 increases risk of false semantic equivalence on nuance-sensitive tasks.
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Safety & Cross-Model Controls */}
      <div className="rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-semibold text-foreground">Safety Boundaries & Invalidation Policies</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-foreground">Allow Cross-Model Reuse</p>
            <p className="text-[11px] text-muted-foreground">
              Reuse responses generated by compatible model tiers (default disabled).
            </p>
          </div>
          <input
            type="checkbox"
            checked={policy.allow_cross_model_cache}
            onChange={(e) => handleChange("allow_cross_model_cache", e.target.checked)}
            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
          />
        </div>

        {policy.allow_cross_model_cache && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-2.5 text-xs text-amber-500">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>
              Enabling cross-model caching may return outputs from smaller models for requests expecting reasoning models.
            </span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-foreground">Stale-While-Revalidate</p>
            <p className="text-[11px] text-muted-foreground">
              Serve slightly expired outputs while dispatching a background refresh job.
            </p>
          </div>
          <input
            type="checkbox"
            checked={policy.stale_while_revalidate}
            onChange={(e) => handleChange("stale_while_revalidate", e.target.checked)}
            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Default TTL (seconds)
            </label>
            <Input
              type="number"
              min="60"
              value={policy.default_ttl}
              onChange={(e) => handleChange("default_ttl", parseInt(e.target.value) || 86400)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Max Entry Size (bytes)
            </label>
            <Input
              type="number"
              min="1024"
              value={policy.max_entry_size}
              onChange={(e) => handleChange("max_entry_size", parseInt(e.target.value) || 500000)}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" variant="default" disabled={saving}>
          <Save className="h-4 w-4 mr-1.5" />
          {saving ? "Saving Policy..." : "Save Cache Policy"}
        </Button>
      </div>
    </form>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  DatabaseZap,
  ArrowLeft,
  Settings,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { cacheService } from "@/services/cache";
import { useWorkspace } from "@/lib/workspaceContext";
import { Button } from "@/components/ui/Button";
import { CachePolicyForm } from "@/components/features/cache/CachePolicyForm";

export default function CacheSettingsPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPolicy = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await cacheService.getPolicy(workspaceId);
      setPolicy(res);
    } catch (err) {
      setError(err?.message || "Failed to load cache policy");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadPolicy();
  }, [loadPolicy]);

  return (
    <div className="space-y-6 p-6 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/50 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/app/cache"
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Back to Cache Dashboard</span>
            </Link>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
            <Settings className="h-6 w-6 text-primary" />
            <span>Workspace Cache Policy Settings</span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Configure TTL bounds, semantic thresholds, cross-model reuse permissions, and storage capacity limits.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadPolicy}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="h-36 rounded-xl border border-border/40 bg-card/50 p-6 animate-pulse"
            />
          ))}
        </div>
      ) : (
        <CachePolicyForm
          initialPolicy={policy}
          workspaceId={workspaceId}
          onSaved={(newPolicy) => setPolicy(newPolicy)}
        />
      )}
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  DatabaseZap,
  RefreshCw,
  Search,
  Trash2,
  Settings,
  ExternalLink,
  Layers,
  Sparkles,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { cacheService } from "@/services/cache";
import { useWorkspace } from "@/lib/workspaceContext";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CacheStatsCards } from "@/components/features/cache/CacheStatsCards";
import { CacheInvalidateModal } from "@/components/features/cache/CacheInvalidateModal";
import { CachePreviewModal } from "@/components/features/cache/CachePreviewModal";

export default function CacheDashboardPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [stats, setStats] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [invalidateModalOpen, setInvalidateModalOpen] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const [statsRes, policyRes] = await Promise.all([
        cacheService.getStats(workspaceId),
        cacheService.getPolicy(workspaceId),
      ]);
      setStats(statsRes);
      setPolicy(policyRes);
    } catch (err) {
      setError(err?.message || "Failed to load cache telemetry");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/50 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5 text-primary">
              <DatabaseZap className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
                Semantic Cache & Intelligent Reuse
                {policy && (
                  <Badge variant={policy.enabled ? "success" : "secondary"}>
                    {policy.enabled ? "ACTIVE" : "DISABLED"}
                  </Badge>
                )}
              </h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                Multi-tenant exact & vector reuse layer preserving correctness, freshness, and strict isolation.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPreviewModalOpen(true)}
          >
            <Search className="h-4 w-4 mr-1.5" />
            Dry-Run Probe
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setInvalidateModalOpen(true)}
          >
            <Trash2 className="h-4 w-4 mr-1.5 text-destructive" />
            Surgical Invalidation
          </Button>
          <Link href="/app/settings/cache">
            <Button variant="default" size="sm">
              <Settings className="h-4 w-4 mr-1.5" />
              Configure Policy
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Section */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Factual Telemetry & Reuse Metrics
          </h2>
          <span className="text-xs text-muted-foreground">
            PostgreSQL + pgvector multi-tenant cache backend
          </span>
        </div>
        <CacheStatsCards stats={stats || {}} loading={loading} />
      </section>

      {/* Architecture Highlights & Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
            <Layers className="h-4 w-4 text-primary" />
            <span>Cache Entries Explorer</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Inspect sanitized entries, verify cryptographic integrity hashes, review timestamps,
            and monitor hit counts.
          </p>
          <div className="pt-2">
            <Link href="/app/cache/entries">
              <Button variant="outline" size="sm" className="w-full">
                <span>View Entries Table</span>
                <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
            <Sparkles className="h-4 w-4 text-indigo-500" />
            <span>Exact & Semantic Matching</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Exact matching runs first with SHA-256 fingerprints. On misses, cosine similarity matches
            using pgvector embeddings with strict scope gates.
          </p>
          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setPreviewModalOpen(true)}
            >
              <span>Test Matching Probe</span>
              <Search className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card/60 p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-foreground font-semibold text-sm">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>Safety & Stampede Protection</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Side-effects, destructive tools, connector mutations, and HITL approvals are never skipped.
            Concurrent duplicate requests are safely coalesced.
          </p>
          <div className="pt-2">
            <Link href="/app/settings/cache">
              <Button variant="outline" size="sm" className="w-full">
                <span>Configure Safety Policies</span>
                <Settings className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Modals */}
      <CacheInvalidateModal
        isOpen={invalidateModalOpen}
        onClose={() => setInvalidateModalOpen(false)}
        workspaceId={workspaceId}
        onInvalidated={loadData}
      />

      <CachePreviewModal
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        workspaceId={workspaceId}
      />
    </div>
  );
}

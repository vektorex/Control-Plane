"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  DatabaseZap,
  ArrowLeft,
  RefreshCw,
  Filter,
  Trash2,
  AlertCircle,
} from "lucide-react";
import { cacheService } from "@/services/cache";
import { useWorkspace } from "@/lib/workspaceContext";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { CacheEntriesTable } from "@/components/features/cache/CacheEntriesTable";
import { CacheEntryDetailDrawer } from "@/components/features/cache/CacheEntryDetailDrawer";
import { CacheInvalidateModal } from "@/components/features/cache/CacheInvalidateModal";

export default function CacheEntriesPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id;

  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [namespaceFilter, setNamespaceFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const [selectedEntry, setSelectedEntry] = useState(null);
  const [invalidateModalOpen, setInvalidateModalOpen] = useState(false);

  const loadEntries = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await cacheService.listEntries({
        workspaceId,
        namespace: namespaceFilter || undefined,
        status: statusFilter || undefined,
        limit,
        offset,
      });
      setEntries(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err?.message || "Failed to load cache entries");
    } finally {
      setLoading(false);
    }
  }, [workspaceId, namespaceFilter, statusFilter, offset]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  const handleDeleteEntry = async (entryId) => {
    if (!confirm("Are you sure you want to invalidate/delete this cache entry?")) return;
    try {
      await cacheService.deleteEntry(entryId, workspaceId);
      setSelectedEntry(null);
      loadEntries();
    } catch (err) {
      alert(err?.message || "Failed to delete entry");
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
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
            <DatabaseZap className="h-6 w-6 text-primary" />
            <span>Cache Entries Explorer</span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Browse and inspect active, expired, or invalidated reusable responses with full cryptographic audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadEntries}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setInvalidateModalOpen(true)}
          >
            <Trash2 className="h-4 w-4 mr-1.5" />
            Surgical Invalidation
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="w-48">
          <Select
            value={namespaceFilter}
            onChange={(e) => {
              setNamespaceFilter(e.target.value);
              setOffset(0);
            }}
            options={[
              { value: "", label: "All Namespaces" },
              { value: "workspace", label: "Workspace" },
              { value: "project", label: "Project" },
              { value: "user", label: "User Private" },
              { value: "global", label: "Global" },
            ]}
          />
        </div>
        <div className="w-44">
          <Select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setOffset(0);
            }}
            options={[
              { value: "", label: "All Statuses" },
              { value: "active", label: "Active" },
              { value: "expired", label: "Expired" },
              { value: "invalidated", label: "Invalidated" },
            ]}
          />
        </div>
        <span className="text-xs text-muted-foreground ml-auto">
          Showing <strong>{entries.length}</strong> of <strong>{total}</strong> entries
        </span>
      </div>

      {/* Table */}
      <CacheEntriesTable
        entries={entries}
        onInspect={(entry) => setSelectedEntry(entry)}
        onDelete={handleDeleteEntry}
        loading={loading}
      />

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0 || loading}
            onClick={() => setOffset((prev) => Math.max(0, prev - limit))}
          >
            Previous
          </Button>
          <span className="text-xs text-muted-foreground">
            Page {Math.floor(offset / limit) + 1} of {Math.ceil(total / limit)}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + limit >= total || loading}
            onClick={() => setOffset((prev) => prev + limit)}
          >
            Next
          </Button>
        </div>
      )}

      {/* Inspection Drawer */}
      <CacheEntryDetailDrawer
        entry={selectedEntry}
        isOpen={Boolean(selectedEntry)}
        onClose={() => setSelectedEntry(null)}
        onDelete={handleDeleteEntry}
      />

      {/* Invalidate Modal */}
      <CacheInvalidateModal
        isOpen={invalidateModalOpen}
        onClose={() => setInvalidateModalOpen(false)}
        workspaceId={workspaceId}
        onInvalidated={loadEntries}
      />
    </div>
  );
}

"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Eye, Trash2 } from "lucide-react";

export function CacheEntriesTable({ entries = [], onInspect, onDelete, loading = false }) {
  const getStatusVariant = (status) => {
    switch (status) {
      case "active":
        return "success";
      case "expired":
        return "secondary";
      case "invalidated":
        return "destructive";
      default:
        return "outline";
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-border/50 bg-card/60 p-8 text-center text-sm text-muted-foreground animate-pulse">
        Loading cache entries...
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border/80 bg-card/40 p-12 text-center">
        <p className="text-sm font-medium text-foreground">No cache entries found</p>
        <p className="text-xs text-muted-foreground mt-1">
          Execute tasks or workflow steps with caching enabled to populate reusable results.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border/50 bg-card/60 shadow-sm backdrop-blur-sm">
      <table className="w-full text-left text-xs">
        <thead className="border-b border-border/50 bg-muted/40 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Namespace</th>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3">Request Summary</th>
            <th className="px-4 py-3 text-center">Hits</th>
            <th className="px-4 py-3">Created</th>
            <th className="px-4 py-3">Expires</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/40 font-mono text-[11px]">
          {entries.map((entry) => (
            <tr
              key={entry.id}
              className="transition-colors hover:bg-muted/30"
            >
              <td className="px-4 py-3 font-sans">
                <Badge variant={getStatusVariant(entry.status)}>
                  {entry.status}
                </Badge>
              </td>
              <td className="px-4 py-3 text-foreground font-sans font-medium">
                {entry.namespace}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {entry.model_id || "default"}
              </td>
              <td className="px-4 py-3 font-sans text-xs text-foreground max-w-xs truncate">
                {entry.normalized_request}
              </td>
              <td className="px-4 py-3 text-center font-semibold text-foreground">
                {entry.hit_count}
              </td>
              <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                {new Date(entry.created_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                {new Date(entry.expires_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3 text-right whitespace-nowrap">
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    title="Inspect Entry"
                    onClick={() => onInspect(entry)}
                  >
                    <Eye className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-destructive hover:bg-destructive/10"
                    title="Delete Entry"
                    onClick={() => onDelete(entry.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

"use client";

import React from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Trash2, Copy, Check } from "lucide-react";

export function CacheEntryDetailDrawer({ entry, isOpen, onClose, onDelete }) {
  const [copied, setCopied] = React.useState(false);

  if (!entry) return null;

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusVariant = (st) => {
    switch (st) {
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Cache Entry Inspection">
      <div className="space-y-4 py-2 text-xs">
        <div className="flex items-center justify-between pb-2 border-b border-border/50">
          <div className="flex items-center gap-2">
            <Badge variant={getStatusVariant(entry.status)}>
              {entry.status?.toUpperCase()}
            </Badge>
            <Badge variant="outline">
              ns: {entry.namespace}
            </Badge>
          </div>
          <span className="text-muted-foreground">
            Hits: <strong className="text-foreground">{entry.hit_count}</strong>
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-muted-foreground block text-[11px] uppercase tracking-wider mb-0.5">
              Entry UUID
            </label>
            <div className="flex items-center gap-1 font-mono text-[11px] truncate bg-muted/40 p-1.5 rounded">
              <span className="truncate">{entry.id}</span>
              <button
                type="button"
                onClick={() => handleCopy(entry.id)}
                className="hover:text-primary shrink-0"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </button>
            </div>
          </div>
          <div>
            <label className="text-muted-foreground block text-[11px] uppercase tracking-wider mb-0.5">
              Model & Provider
            </label>
            <div className="font-mono text-[11px] bg-muted/40 p-1.5 rounded truncate">
              {entry.model_id || "default"} ({entry.model_provider || "auto"})
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-muted-foreground block text-[11px] uppercase tracking-wider mb-0.5">
              Created At
            </label>
            <div className="text-[11px] bg-muted/40 p-1.5 rounded">
              {new Date(entry.created_at).toLocaleString()}
            </div>
          </div>
          <div>
            <label className="text-muted-foreground block text-[11px] uppercase tracking-wider mb-0.5">
              Expires At
            </label>
            <div className="text-[11px] bg-muted/40 p-1.5 rounded">
              {new Date(entry.expires_at).toLocaleString()}
            </div>
          </div>
        </div>

        <div className="space-y-2 pt-2 border-t border-border/50">
          <label className="text-muted-foreground block text-[11px] uppercase tracking-wider">
            Cryptographic Integrity Fingerprints
          </label>
          <div className="grid grid-cols-1 gap-1.5 font-mono text-[11px]">
            <div className="flex justify-between bg-muted/30 p-1.5 rounded">
              <span className="text-muted-foreground">Request Fingerprint:</span>
              <span className="truncate max-w-[240px]">{entry.request_fingerprint}</span>
            </div>
            {entry.prompt_version_id && (
              <div className="flex justify-between bg-muted/30 p-1.5 rounded">
                <span className="text-muted-foreground">Prompt Version:</span>
                <span className="truncate max-w-[240px]">{entry.prompt_version_id}</span>
              </div>
            )}
            {entry.artifact_hash && (
              <div className="flex justify-between bg-muted/30 p-1.5 rounded">
                <span className="text-muted-foreground">Artifact Hash:</span>
                <span className="truncate max-w-[240px]">{entry.artifact_hash}</span>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-1.5 pt-2 border-t border-border/50">
          <label className="text-muted-foreground block text-[11px] uppercase tracking-wider">
            Normalized Request (Sanitized)
          </label>
          <div className="max-h-24 overflow-y-auto bg-muted/40 p-2.5 rounded font-mono text-[11px] whitespace-pre-wrap">
            {entry.normalized_request}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-muted-foreground block text-[11px] uppercase tracking-wider">
            Cached Response Content (Sanitized)
          </label>
          <div className="max-h-40 overflow-y-auto bg-muted/40 p-2.5 rounded text-xs whitespace-pre-wrap">
            {entry.response_content}
          </div>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => onDelete(entry.id)}
          >
            <Trash2 className="h-3.5 w-3.5 mr-1.5" />
            Delete Entry
          </Button>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}

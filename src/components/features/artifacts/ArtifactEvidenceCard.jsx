"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { Clock, FileText, Image, Table, ShieldCheck, ExternalLink } from "lucide-react";

export function ArtifactEvidenceCard({ evidence, onJumpToTimestamp, onHighlightRegion }) {
  if (!evidence) return null;

  const {
    page,
    timestamp,
    region,
    source_text,
    part_id,
    metadata = {},
  } = evidence;

  const confidence = metadata?.confidence != null ? Math.round(metadata.confidence * 100) : null;
  const citationType = metadata?.citation_type || (timestamp != null ? "audio_transcript" : page != null ? "document_page" : region ? "image_region" : "extracted_part");

  const formatTimestamp = (secs) => {
    if (secs == null) return null;
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 hover:border-zinc-700 transition-colors space-y-2 text-xs">
      <div className="flex items-center justify-between text-zinc-400">
        <div className="flex items-center gap-1.5 font-medium text-zinc-300">
          {timestamp != null && (
            <span className="flex items-center gap-1 text-cyan-400">
              <Clock className="h-3.5 w-3.5" />
              {formatTimestamp(timestamp)}
            </span>
          )}
          {page != null && (
            <span className="flex items-center gap-1 text-amber-400">
              <FileText className="h-3.5 w-3.5" />
              Page {page}
            </span>
          )}
          {region && (
            <span className="flex items-center gap-1 text-purple-400">
              <Image className="h-3.5 w-3.5" />
              Region [{Array.isArray(region) ? region.join(", ") : JSON.stringify(region)}]
            </span>
          )}
          {metadata?.sheet && (
            <span className="flex items-center gap-1 text-emerald-400">
              <Table className="h-3.5 w-3.5" />
              Sheet: {metadata.sheet} {metadata.row ? `(Row ${metadata.row})` : ""}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {confidence !== null && (
            <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-700">
              {confidence}% match
            </Badge>
          )}
          <Badge variant="secondary" className="text-[10px] uppercase">
            {citationType}
          </Badge>
        </div>
      </div>

      {source_text && (
        <div className="bg-zinc-950 p-2 rounded border border-zinc-800/80 font-mono text-zinc-300 text-[11px] leading-relaxed break-words">
          &ldquo;{source_text}&rdquo;
        </div>
      )}

      <div className="flex items-center justify-between pt-1 text-[10px] text-zinc-500">
        <span className="flex items-center gap-1">
          <ShieldCheck className="h-3 w-3 text-emerald-500" />
          Verified provenance
        </span>
        {timestamp != null && onJumpToTimestamp && (
          <button
            onClick={() => onJumpToTimestamp(timestamp)}
            className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            Jump to audio/video
            <ExternalLink className="h-3 w-3" />
          </button>
        )}
        {region && onHighlightRegion && (
          <button
            onClick={() => onHighlightRegion(region)}
            className="text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors"
          >
            Highlight region
            <ExternalLink className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  );
}

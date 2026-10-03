"use client";

import React from "react";
import { ImageViewer } from "./ImageViewer";
import { PDFViewer } from "./PDFViewer";
import { AudioViewer } from "./AudioViewer";
import { VideoViewer } from "./VideoViewer";
import { TableViewer } from "./TableViewer";
import { File, AlertTriangle } from "lucide-react";

export function ArtifactViewer({
  artifact,
  parts = [],
  activeRegion = null,
  activeTimestamp = null,
  activePage = 1,
  onSelectTimestamp,
  onSelectFrame,
  onSelectPage,
}) {
  if (!artifact) {
    return (
      <div className="h-64 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center justify-center text-zinc-500 text-xs">
        No artifact loaded.
      </div>
    );
  }

  const type = (artifact.artifact_type || "unknown").toLowerCase();

  switch (type) {
    case "image":
      return <ImageViewer artifact={artifact} parts={parts} activeRegion={activeRegion} />;
    case "document":
      return <PDFViewer artifact={artifact} parts={parts} activePage={activePage} onSelectPage={onSelectPage} />;
    case "audio":
      return <AudioViewer artifact={artifact} parts={parts} onSelectTimestamp={onSelectTimestamp} />;
    case "video":
      return <VideoViewer artifact={artifact} parts={parts} onSelectFrame={onSelectFrame} />;
    case "spreadsheet":
    case "table":
      return <TableViewer artifact={artifact} parts={parts} />;
    case "text":
      return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 h-[550px] overflow-y-auto">
          <pre className="text-xs font-mono text-zinc-200 whitespace-pre-wrap leading-relaxed">
            {parts[0]?.text_content || "Plain text artifact"}
          </pre>
        </div>
      );
    default:
      return (
        <div className="h-[400px] bg-zinc-900 border border-zinc-800 rounded-xl flex flex-col items-center justify-center text-zinc-400 gap-2">
          <File className="h-12 w-12 text-zinc-600" />
          <p className="text-sm font-medium">Binary / Archive Artifact</p>
          <p className="text-xs text-zinc-500 font-mono">
            {artifact.filename} ({artifact.mime_type})
          </p>
          <p className="text-[11px] text-zinc-600">
            Raw media cannot be previewed directly in browser safely.
          </p>
        </div>
      );
  }
}

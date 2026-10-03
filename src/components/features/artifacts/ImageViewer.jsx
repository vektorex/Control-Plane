"use client";

import React, { useState, useRef } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, FileText, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function ImageViewer({ artifact, parts = [], activeRegion = null }) {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [activeTab, setActiveTab] = useState("preview"); // "preview" | "ocr"
  const containerRef = useRef(null);

  // Find image part or use base storage reference
  const imagePart = parts.find((p) => p.part_type === "image");
  const textPart = parts.find((p) => p.part_type === "text" || p.metadata?.is_ocr);

  const meta = artifact?.metadata || {};
  const dimensions = meta.dimensions || (imagePart?.metadata?.dimensions) || null;

  const handleZoomIn = () => setScale((s) => Math.min(s + 0.25, 4));
  const handleZoomOut = () => setScale((s) => Math.max(s - 0.25, 0.5));
  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (scale <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Compute bounding box styling safely if 4 coordinates are provided
  const renderBoundingBox = (region) => {
    if (!region || !Array.isArray(region) || region.length < 4) return null;
    const [ymin, xmin, ymax, xmax] = region;
    // Assuming normalized [0, 1000] or [0, 1]
    const isNormalized1000 = ymax > 1 || xmax > 1;
    const factor = isNormalized1000 ? 0.1 : 100;

    const top = `${ymin * factor}%`;
    const left = `${xmin * factor}%`;
    const height = `${(ymax - ymin) * factor}%`;
    const width = `${(xmax - xmin) * factor}%`;

    return (
      <div
        className="absolute border-2 border-purple-500 bg-purple-500/20 pointer-events-none rounded transition-all animate-pulse"
        style={{ top, left, width, height }}
      >
        <span className="absolute -top-5 left-0 text-[10px] font-mono bg-purple-600 text-white px-1 rounded">
          Evidence Region
        </span>
      </div>
    );
  };

  // Image source URL or placeholder SVG
  const imageUrl = artifact?.storage_reference
    ? `/api/artifacts/${artifact.id}/raw`
    : null;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden flex flex-col h-[550px]">
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-950/60">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("preview")}
            className={`px-3 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === "preview"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <ImageIcon className="h-3.5 w-3.5 text-blue-400" />
            Image View
          </button>
          <button
            onClick={() => setActiveTab("ocr")}
            className={`px-3 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === "ocr"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <FileText className="h-3.5 w-3.5 text-amber-400" />
            Extracted OCR Text
          </button>
        </div>

        {activeTab === "preview" && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-500">
              {Math.round(scale * 100)}%
            </span>
            <div className="flex items-center bg-zinc-800/80 rounded border border-zinc-700">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-zinc-300"
                onClick={handleZoomOut}
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-zinc-300"
                onClick={handleReset}
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-zinc-300"
                onClick={handleZoomIn}
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="relative flex-1 bg-zinc-950 flex items-center justify-center overflow-hidden">
        {activeTab === "preview" ? (
          <div
            ref={containerRef}
            className={`w-full h-full flex items-center justify-center ${
              scale > 1 ? "cursor-grab active:cursor-grabbing" : ""
            }`}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            <div
              className="relative transition-transform duration-75 select-none"
              style={{
                transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
              }}
            >
              {imageUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={imageUrl}
                  alt={artifact?.filename || "Multimodal Image"}
                  className="max-h-[460px] max-w-full object-contain rounded shadow-lg"
                  draggable={false}
                />
              ) : (
                <div className="h-64 w-80 bg-zinc-900 border border-zinc-800 rounded flex flex-col items-center justify-center text-zinc-500">
                  <ImageIcon className="h-12 w-12 text-zinc-600 mb-2" />
                  <p className="text-xs">Image reference available</p>
                  <p className="text-[10px] text-zinc-600 font-mono mt-1">
                    {artifact?.filename}
                  </p>
                </div>
              )}
              {activeRegion && renderBoundingBox(activeRegion)}
            </div>
          </div>
        ) : (
          <div className="w-full h-full p-6 overflow-y-auto">
            {textPart?.text_content ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-zinc-400">
                  <span>OCR Provider: {textPart.metadata?.ocr_provider || "Standard"}</span>
                  <Badge variant="outline" className="text-amber-400 border-amber-800/60">
                    Untrusted Content
                  </Badge>
                </div>
                <pre className="bg-zinc-900 p-4 rounded-lg text-xs font-mono text-zinc-200 whitespace-pre-wrap leading-relaxed border border-zinc-800">
                  {textPart.text_content}
                </pre>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-xs">
                <FileText className="h-8 w-8 text-zinc-600 mb-2" />
                <p>No OCR text extracted for this image.</p>
                <p className="text-[10px] text-zinc-600 mt-1">
                  Trigger extraction or verify provider capability.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Metadata Footer */}
      <div className="px-4 py-2 bg-zinc-950/80 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-4">
          <span>Format: <strong className="text-zinc-200">{artifact?.mime_type || "image"}</strong></span>
          {dimensions && (
            <span>
              Dimensions:{" "}
              <strong className="text-zinc-200">
                {dimensions.width} × {dimensions.height} px
              </strong>
            </span>
          )}
          <span>Size: <strong className="text-zinc-200">{((artifact?.size_bytes || 0) / 1024).toFixed(1)} KB</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-[10px]">
            Safe Resolution
          </Badge>
        </div>
      </div>
    </div>
  );
}

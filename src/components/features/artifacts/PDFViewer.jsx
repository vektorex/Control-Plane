"use client";

import React, { useState } from "react";
import { ChevronLeft, ChevronRight, FileText, Search, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function PDFViewer({ artifact, parts = [], activePage = 1, onSelectPage }) {
  const [currentPage, setCurrentPage] = useState(activePage || 1);
  const [searchTerm, setSearchTerm] = useState("");

  // Filter text parts or page parts
  const textParts = parts.filter((p) => p.part_type === "text" || p.part_type === "structured_data");

  const totalPages = artifact?.metadata?.page_count || Math.max(textParts.length, 1);

  const activePart = textParts.find(
    (p) => (p.metadata?.page_number || p.sequence_number + 1) === currentPage
  ) || textParts[0];

  const handlePrev = () => {
    if (currentPage > 1) {
      const p = currentPage - 1;
      setCurrentPage(p);
      if (onSelectPage) onSelectPage(p);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      const p = currentPage + 1;
      setCurrentPage(p);
      if (onSelectPage) onSelectPage(p);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden flex flex-col h-[550px]">
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-950/60">
        <div className="flex items-center gap-3">
          <BookOpen className="h-4 w-4 text-amber-400" />
          <span className="text-xs font-medium text-zinc-200">
            Document Intelligence
          </span>
          <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-700">
            {totalPages} Pages
          </Badge>
        </div>

        {/* Page Nav */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-zinc-300"
            disabled={currentPage <= 1}
            onClick={handlePrev}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs font-mono text-zinc-300">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 text-zinc-300"
            disabled={currentPage >= totalPages}
            onClick={handleNext}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Text & Page Content */}
      <div className="flex-1 bg-zinc-950 p-6 overflow-y-auto space-y-4">
        {activePart?.text_content ? (
          <div className="max-w-3xl mx-auto space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2 text-xs text-zinc-400">
              <span>Section / Page {currentPage}</span>
              <span className="font-mono text-[10px] text-zinc-500">
                Hash: {activePart.content_hash?.slice(0, 12)}...
              </span>
            </div>

            <div className="prose prose-invert max-w-none text-xs leading-relaxed font-sans text-zinc-300 whitespace-pre-wrap bg-zinc-900/60 p-5 rounded-lg border border-zinc-800">
              {activePart.text_content}
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-xs">
            <FileText className="h-10 w-10 text-zinc-600 mb-2" />
            <p>No extracted text available for Page {currentPage}.</p>
            <p className="text-[10px] text-zinc-600 mt-1">
              Document processing extracts page chunks into structured parts.
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-zinc-950/80 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-3">
          <span>File: <strong className="text-zinc-200">{artifact?.filename}</strong></span>
          <span>Size: <strong className="text-zinc-200">{((artifact?.size_bytes || 0) / (1024 * 1024)).toFixed(2)} MB</strong></span>
        </div>
        <Badge variant="secondary" className="text-[10px]">
          Bounded Page Extraction
        </Badge>
      </div>
    </div>
  );
}

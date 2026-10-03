"use client";

import React, { useState } from "react";
import { Table, Columns, FileSpreadsheet, Eye, Code } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export function TableViewer({ artifact, parts = [] }) {
  const [activeTab, setActiveTab] = useState("preview"); // "preview" | "schema" | "markdown"
  const [selectedRange, setSelectedRange] = useState(null);

  // Table part
  const tablePart = parts.find((p) => p.part_type === "table" || p.part_type === "structured_data");
  const meta = artifact?.metadata || {};
  const partMeta = tablePart?.metadata || {};

  const columns = partMeta.columns || meta.columns || [];
  const rows = partMeta.preview_rows || meta.preview_rows || [];
  const totalRows = partMeta.total_rows || meta.row_count || rows.length;
  const totalCols = columns.length || meta.column_count || (rows[0] ? rows[0].length : 0);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden flex flex-col h-[550px]">
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-950/60">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-medium text-zinc-200">
            Structured Data & Table Intelligence
          </span>
          <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-700">
            {totalRows} Rows × {totalCols} Cols
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("preview")}
            className={`px-3 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === "preview"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Table className="h-3.5 w-3.5 text-emerald-400" />
            Grid Preview
          </button>
          <button
            onClick={() => setActiveTab("schema")}
            className={`px-3 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === "schema"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Columns className="h-3.5 w-3.5 text-blue-400" />
            Schema Definition
          </button>
          <button
            onClick={() => setActiveTab("markdown")}
            className={`px-3 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === "markdown"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Code className="h-3.5 w-3.5 text-amber-400" />
            Markdown Summary
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 bg-zinc-950 overflow-auto p-4">
        {activeTab === "preview" ? (
          rows.length > 0 ? (
            <div className="border border-zinc-800 rounded-lg overflow-hidden max-w-full">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead className="bg-zinc-900 border-b border-zinc-800 sticky top-0 text-zinc-400 font-semibold">
                  <tr>
                    <th className="p-2 border-r border-zinc-800 w-10 text-center text-zinc-500">#</th>
                    {columns.map((col, idx) => (
                      <th key={idx} className="p-2 border-r border-zinc-800 whitespace-nowrap text-zinc-300">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60 bg-zinc-950">
                  {rows.slice(0, 50).map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-zinc-900/60 transition-colors">
                      <td className="p-2 border-r border-zinc-800 text-center text-zinc-500 text-[10px]">
                        {rIdx + 1}
                      </td>
                      {(Array.isArray(row) ? row : Object.values(row)).map((cell, cIdx) => (
                        <td
                          key={cIdx}
                          className="p-2 border-r border-zinc-800 whitespace-nowrap text-zinc-200 text-[11px] truncate max-w-[200px]"
                          title={String(cell ?? "")}
                        >
                          {String(cell ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {totalRows > 50 && (
                <div className="p-2 bg-zinc-900/80 text-center text-[11px] text-zinc-500 border-t border-zinc-800">
                  Showing first 50 rows of {totalRows} (bounded for browser performance).
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-xs">
              <Table className="h-8 w-8 text-zinc-600 mb-2" />
              <p>No preview rows extracted for table.</p>
            </div>
          )
        ) : activeTab === "schema" ? (
          <div className="max-w-2xl mx-auto space-y-4">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Detected Columns & Field Types
            </h4>
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg divide-y divide-zinc-800">
              {columns.map((col, idx) => (
                <div key={idx} className="p-3 flex items-center justify-between text-xs">
                  <span className="font-mono text-zinc-200">{col}</span>
                  <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-800">
                    Column #{idx + 1}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            <pre className="bg-zinc-900 p-4 rounded-lg font-mono text-xs text-zinc-300 whitespace-pre-wrap overflow-x-auto border border-zinc-800 leading-relaxed">
              {tablePart?.text_content || "No markdown representation generated."}
            </pre>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-zinc-950/80 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-3">
          <span>File: <strong className="text-zinc-200">{artifact?.filename}</strong></span>
          <span>Size: <strong className="text-zinc-200">{((artifact?.size_bytes || 0) / 1024).toFixed(1)} KB</strong></span>
        </div>
        <Badge variant="secondary" className="text-[10px]">
          Bounded Table Budget Controls
        </Badge>
      </div>
    </div>
  );
}

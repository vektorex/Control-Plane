"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  FileImage,
  Upload,
  RefreshCw,
  Trash2,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Headphones,
  Film,
  Table as TableIcon,
  Eye,
  Loader2,
} from "lucide-react";
import { artifactService } from "@/services/artifacts";
import { projectService } from "@/services/projects";
import { useWorkspace } from "@/lib/workspaceContext";
import { ArtifactUploadModal } from "@/components/features/artifacts/ArtifactUploadModal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function getTypeIcon(type = "") {
  switch (type.toLowerCase()) {
    case "image":
      return <FileImage className="w-4 h-4 text-purple-400" />;
    case "audio":
      return <Headphones className="w-4 h-4 text-cyan-400" />;
    case "video":
      return <Film className="w-4 h-4 text-pink-400" />;
    case "spreadsheet":
    case "table":
      return <TableIcon className="w-4 h-4 text-emerald-400" />;
    case "document":
      return <FileText className="w-4 h-4 text-amber-400" />;
    default:
      return <FileText className="w-4 h-4 text-zinc-400" />;
  }
}

function StatusBadge({ status }) {
  switch (status) {
    case "ready":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/60 border border-emerald-500/30 text-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Ready
        </span>
      );
    case "processing":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-950/60 border border-blue-500/30 text-blue-300 animate-pulse">
          <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
          Processing
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/60 border border-rose-500/30 text-rose-300">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          Failed
        </span>
      );
    case "archived":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-800/80 border border-zinc-700 text-zinc-400">
          Archived
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/60 border border-amber-500/30 text-amber-300">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          Uploaded
        </span>
      );
  }
}

export default function ArtifactsLibraryPage() {
  const { currentWorkspace } = useWorkspace();
  const [artifacts, setArtifacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const loadArtifacts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { limit: 100 };
      if (currentWorkspace?.id) params.workspace_id = currentWorkspace.id;
      if (typeFilter !== "all") params.artifact_type = typeFilter;
      if (statusFilter !== "all") params.status = statusFilter;

      const data = await artifactService.listArtifacts(params);
      setArtifacts(Array.isArray(data) ? data : data?.artifacts || []);
    } catch (err) {
      console.error("Failed to load artifacts:", err);
      setError(err?.message || "Failed to load artifacts.");
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace?.id, typeFilter, statusFilter]);

  useEffect(() => {
    loadArtifacts();
  }, [loadArtifacts]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this artifact?")) return;
    try {
      await artifactService.deleteArtifact(id);
      setArtifacts((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      alert("Failed to delete artifact: " + err.message);
    }
  };

  const handleProcess = async (id, e) => {
    e.stopPropagation();
    try {
      await artifactService.processArtifact(id);
      loadArtifacts();
    } catch (err) {
      alert("Failed to trigger processing: " + err.message);
    }
  };

  const filteredArtifacts = artifacts.filter((a) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      a.filename?.toLowerCase().includes(term) ||
      a.artifact_type?.toLowerCase().includes(term) ||
      a.mime_type?.toLowerCase().includes(term)
    );
  });

  // Summary Metrics
  const readyCount = artifacts.filter((a) => a.status === "ready").length;
  const mediaCount = artifacts.filter((a) => ["image", "audio", "video"].includes(a.artifact_type?.toLowerCase())).length;
  const tableDocCount = artifacts.filter((a) => ["document", "spreadsheet", "table"].includes(a.artifact_type?.toLowerCase())).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 py-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <FileImage className="h-6 w-6 text-purple-400" />
            Artifact Intelligence
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Multimodal asset library with grounded extraction across images, PDFs, audio, video frames, and tables.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadArtifacts}
            disabled={loading}
            className="text-zinc-300 border-zinc-700"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setIsUploadOpen(true)}
            className="bg-purple-600 hover:bg-purple-500 text-white"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Artifact
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-xs font-medium text-zinc-400">Total Artifacts</p>
          <p className="text-2xl font-bold text-zinc-100 mt-1">{artifacts.length}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-xs font-medium text-zinc-400">Ready & Indexed</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{readyCount}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-xs font-medium text-zinc-400">Vision & Audio/Video</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">{mediaCount}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-xs font-medium text-zinc-400">Docs & Structured Tables</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">{tableDocCount}</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-zinc-900/60 p-3 rounded-xl border border-zinc-800">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search artifacts by filename or MIME type..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-700"
          >
            <option value="all">All Media Types</option>
            <option value="image">Images</option>
            <option value="document">Documents (PDF)</option>
            <option value="audio">Audio</option>
            <option value="video">Video</option>
            <option value="spreadsheet">Tables / CSV</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-700"
          >
            <option value="all">All Statuses</option>
            <option value="ready">Ready</option>
            <option value="processing">Processing</option>
            <option value="uploaded">Uploaded</option>
            <option value="failed">Failed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Artifacts Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-zinc-500 text-xs flex flex-col items-center justify-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
            Loading artifacts library...
          </div>
        ) : filteredArtifacts.length === 0 ? (
          <div className="p-12 text-center text-zinc-500 text-xs flex flex-col items-center justify-center gap-3">
            <FileImage className="h-10 w-10 text-zinc-700" />
            <p className="text-zinc-400 font-medium">No multimodal artifacts found</p>
            <p className="text-zinc-600 max-w-sm">
              Upload images, PDFs, audio recordings, video clips, or spreadsheets to use them as first-class context in tasks and workflows.
            </p>
            <Button size="sm" onClick={() => setIsUploadOpen(true)} className="mt-2">
              <Upload className="h-3.5 w-3.5 mr-1.5" />
              Upload First Artifact
            </Button>
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-zinc-950/80 border-b border-zinc-800 text-zinc-400 font-medium">
              <tr>
                <th className="p-3.5">Filename</th>
                <th className="p-3.5">Type</th>
                <th className="p-3.5">Size</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Created</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {filteredArtifacts.map((art) => (
                <tr
                  key={art.id}
                  className="hover:bg-zinc-800/40 transition-colors group cursor-pointer"
                  onClick={() => window.location.href = `/app/artifacts/${art.id}`}
                >
                  <td className="p-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-zinc-800/80 border border-zinc-700/60">
                        {getTypeIcon(art.artifact_type)}
                      </div>
                      <div>
                        <p className="font-medium text-zinc-200 group-hover:text-purple-400 transition-colors">
                          {art.filename}
                        </p>
                        <p className="text-[10px] text-zinc-500 font-mono">
                          {art.mime_type}
                        </p>
                      </div>
                    </div>
                  </td>

                  <td className="p-3.5">
                    <Badge variant="outline" className="capitalize text-[11px] border-zinc-700 text-zinc-300">
                      {art.artifact_type || "unknown"}
                    </Badge>
                  </td>

                  <td className="p-3.5 text-zinc-400 font-mono">
                    {formatBytes(art.size_bytes)}
                  </td>

                  <td className="p-3.5">
                    <StatusBadge status={art.status} />
                  </td>

                  <td className="p-3.5 text-zinc-400">
                    {art.created_at ? new Date(art.created_at).toLocaleDateString() : "—"}
                  </td>

                  <td className="p-3.5 text-right">
                    <div className="inline-flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <Link href={`/app/artifacts/${art.id}`}>
                        <Button variant="ghost" size="sm" className="h-7 px-2 text-zinc-300 hover:text-white">
                          <Eye className="h-3.5 w-3.5 mr-1" />
                          View
                        </Button>
                      </Link>
                      {art.status !== "processing" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2 text-blue-400 hover:text-blue-300"
                          onClick={(e) => handleProcess(art.id, e)}
                        >
                          <RefreshCw className="h-3.5 w-3.5 mr-1" />
                          Extract
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-rose-400 hover:text-rose-300"
                        onClick={(e) => handleDelete(art.id, e)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Upload Modal */}
      <ArtifactUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploaded={() => loadArtifacts()}
      />
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Files,
  Upload,
  RefreshCw,
  Trash2,
  FileText,
  FileCode,
  FileCheck,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
  Database,
  Layers,
  ChevronRight,
  ExternalLink,
  Search,
  Filter,
  X,
  Sparkles,
  Info,
  Loader2,
} from "lucide-react";
import { documentService } from "@/services/documents";
import { projectService } from "@/services/projects";
import { useWorkspace } from "@/lib/workspaceContext";

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function getFileIcon(filename = "", mimeType = "") {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "pdf" || mimeType.includes("pdf")) {
    return <FileText className="w-5 h-5 text-rose-400" />;
  }
  if (ext === "md" || ext === "markdown") {
    return <FileCode className="w-5 h-5 text-emerald-400" />;
  }
  if (ext === "docx" || ext === "doc" || mimeType.includes("word")) {
    return <FileText className="w-5 h-5 text-blue-400" />;
  }
  return <FileText className="w-5 h-5 text-indigo-400" />;
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
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/60 border border-amber-500/30 text-amber-300">
          <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
          Processing
        </span>
      );
    case "pending":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          Pending
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/60 border border-rose-500/30 text-rose-300">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          Failed
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300">
          {status}
        </span>
      );
  }
}

export default function DocumentsPage() {
  const { currentWorkspace } = useWorkspace();
  const [documents, setDocuments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [projectFilter, setProjectFilter] = useState("all");

  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProjectId, setUploadProjectId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);

  // Inspect chunks modal state
  const [inspectDoc, setInspectDoc] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  // Action states
  const [deletingId, setDeletingId] = useState(null);
  const [reprocessingId, setReprocessingId] = useState(null);

  const fetchDocuments = useCallback(
    async (isManualRefresh = false) => {
      if (!currentWorkspace?.id) return;
      if (isManualRefresh) setRefreshing(true);

      try {
        const params = {};
        if (projectFilter !== "all") params.project_id = projectFilter;
        if (statusFilter !== "all") params.status = statusFilter;

        const res = await documentService.listWorkspaceDocuments(currentWorkspace.id, params);
        setDocuments(res.items || []);
      } catch (err) {
        console.error("Failed to load documents:", err);
      } finally {
        setLoading(false);
        if (isManualRefresh) setRefreshing(false);
      }
    },
    [currentWorkspace?.id, projectFilter, statusFilter]
  );

  const fetchProjects = useCallback(async () => {
    if (!currentWorkspace?.id) return;
    try {
      const res = await projectService.listProjects({ workspace_id: currentWorkspace.id });
      setProjects(res.projects || []);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    }
  }, [currentWorkspace?.id]);

  useEffect(() => {
    fetchDocuments();
    fetchProjects();
  }, [fetchDocuments, fetchProjects]);

  // Polling for pending/processing documents
  useEffect(() => {
    const hasActiveProcessing = documents.some(
      (d) => d.status === "pending" || d.status === "processing"
    );

    if (!hasActiveProcessing) return;

    const interval = setInterval(() => {
      fetchDocuments();
    }, 2500);

    return () => clearInterval(interval);
  }, [documents, fetchDocuments]);

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile || !currentWorkspace?.id) return;

    setUploading(true);
    setUploadError(null);

    try {
      await documentService.uploadDocument(currentWorkspace.id, selectedFile, {
        projectId: uploadProjectId || undefined,
      });

      setSelectedFile(null);
      setUploadProjectId("");
      setUploadModalOpen(false);
      await fetchDocuments();
    } catch (err) {
      setUploadError(err.message || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!confirm("Are you sure you want to delete this document and all its indexed vector chunks?")) {
      return;
    }

    setDeletingId(docId);
    try {
      await documentService.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (inspectDoc?.id === docId) {
        setInspectDoc(null);
      }
    } catch (err) {
      alert("Failed to delete document: " + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleReprocessDocument = async (docId) => {
    setReprocessingId(docId);
    try {
      await documentService.reprocessDocument(docId);
      await fetchDocuments();
    } catch (err) {
      alert("Failed to reprocess document: " + err.message);
    } finally {
      setReprocessingId(null);
    }
  };

  const handleInspectChunks = async (doc) => {
    setInspectDoc(doc);
    setLoadingChunks(true);
    setChunks([]);

    try {
      const res = await documentService.getDocumentChunks(doc.id, { limit: 100 });
      setChunks(res.items || []);
    } catch (err) {
      console.error("Failed to fetch chunks:", err);
    } finally {
      setLoadingChunks(false);
    }
  };

  // Filtered list
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const totalDocs = documents.length;
  const readyDocs = documents.filter((d) => d.status === "ready").length;
  const processingDocs = documents.filter(
    (d) => d.status === "processing" || d.status === "pending"
  ).length;
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
            <Database className="w-3.5 h-3.5" />
            Knowledge Base & RAG Index
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Document Ingestion & Chunks
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload domain knowledge in PDF, TXT, Markdown, or DOCX formats for hybrid vector + keyword retrieval.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchDocuments(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-300 bg-slate-900 border border-slate-700/80 rounded-lg hover:bg-slate-800 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
            Refresh
          </button>
          <button
            onClick={() => {
              setSelectedFile(null);
              setUploadError(null);
              setUploadModalOpen(true);
            }}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 shadow-md shadow-indigo-900/30 transition-all"
          >
            <Upload className="w-4 h-4" />
            Upload Document
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Files className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Total Documents</div>
            <div className="text-xl font-bold text-slate-100">{totalDocs}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Indexed & Ready</div>
            <div className="text-xl font-bold text-emerald-300">{readyDocs}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Loader2 className={`w-5 h-5 ${processingDocs > 0 ? "animate-spin" : ""}`} />
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Ingesting Queue</div>
            <div className="text-xl font-bold text-amber-300">{processingDocs}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Vector Chunks</div>
            <div className="text-xl font-bold text-purple-300">{totalChunks}</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 p-3 bg-slate-900/40 border border-slate-800/80 rounded-xl">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
          {/* Project Filter */}
          <select
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-slate-950/80 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="ready">Ready</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Document List Table / Cards */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-slate-900/30 border border-slate-800/60 rounded-xl space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          <p className="text-xs text-slate-400">Loading workspace documents...</p>
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 px-4 bg-slate-900/20 border border-dashed border-slate-800 rounded-xl text-center space-y-3">
          <div className="p-3 rounded-full bg-slate-800/80 text-slate-400">
            <Files className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">No documents found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm">
              Upload PDF, Markdown, TXT, or DOCX files to enable Hybrid RAG retrieval for your tasks.
            </p>
          </div>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-300 bg-indigo-950/50 border border-indigo-500/30 rounded-lg hover:bg-indigo-900/50 transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload First Document
          </button>
        </div>
      ) : (
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 text-[10px]">
                <tr>
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-4">Project</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Chunks</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredDocuments.map((doc) => {
                  const proj = projects.find((p) => p.id === doc.project_id);
                  const isProcessing = doc.status === "processing" || doc.status === "pending";

                  return (
                    <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors group">
                      <td className="py-3.5 px-4 font-medium text-slate-100">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50 shrink-0">
                            {getFileIcon(doc.filename, doc.mime_type)}
                          </div>
                          <div className="min-w-0">
                            <div className="truncate font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors">
                              {doc.filename}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono truncate">
                              {doc.original_filename !== doc.filename ? doc.original_filename : doc.mime_type}
                            </div>
                            {doc.error_message && (
                              <div className="mt-1 text-[11px] text-rose-400 bg-rose-950/40 border border-rose-800/30 px-2 py-0.5 rounded flex items-center gap-1">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                <span className="truncate">{doc.error_message}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        {proj ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/50 text-slate-300 text-[11px]">
                            {proj.name}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Workspace-wide</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <StatusBadge status={doc.status} />
                      </td>

                      <td className="py-3.5 px-4 font-mono text-slate-400">
                        {formatBytes(doc.file_size)}
                      </td>

                      <td className="py-3.5 px-4">
                        {doc.status === "ready" ? (
                          <button
                            onClick={() => handleInspectChunks(doc)}
                            className="inline-flex items-center gap-1 font-mono text-indigo-400 hover:text-indigo-300 bg-indigo-950/40 border border-indigo-500/20 px-2 py-0.5 rounded hover:bg-indigo-900/50 transition-colors"
                          >
                            <Layers className="w-3 h-3" />
                            {doc.chunk_count} chunks
                          </button>
                        ) : (
                          <span className="text-slate-500 font-mono">—</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 text-[11px] whitespace-nowrap">
                        {new Date(doc.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {doc.status === "ready" && (
                            <button
                              onClick={() => handleInspectChunks(doc)}
                              title="Inspect Vector Chunks"
                              className="p-1.5 text-slate-400 hover:text-indigo-300 hover:bg-slate-800 rounded-lg transition-colors"
                            >
                              <Layers className="w-4 h-4" />
                            </button>
                          )}

                          <button
                            onClick={() => handleReprocessDocument(doc.id)}
                            disabled={reprocessingId === doc.id || isProcessing}
                            title="Reprocess Document"
                            className="p-1.5 text-slate-400 hover:text-cyan-300 hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-40"
                          >
                            <RefreshCw
                              className={`w-4 h-4 ${reprocessingId === doc.id ? "animate-spin text-cyan-400" : ""}`}
                            />
                          </button>

                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            disabled={deletingId === doc.id}
                            title="Delete Document"
                            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors disabled:opacity-40"
                          >
                            {deletingId === doc.id ? (
                              <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-slate-100 font-semibold text-base">
                <Upload className="w-5 h-5 text-indigo-400" />
                Upload Knowledge Document
              </div>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {uploadError && (
              <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              {/* File Dropzone */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Select File (PDF, TXT, Markdown, DOCX)
                </label>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  accept=".pdf,.txt,.md,.markdown,.docx"
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-950/40 group"
                >
                  {selectedFile ? (
                    <div className="flex items-center justify-center gap-3">
                      <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                        {getFileIcon(selectedFile.name, selectedFile.type)}
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-semibold text-slate-100">{selectedFile.name}</div>
                        <div className="text-[11px] text-slate-400">{formatBytes(selectedFile.size)}</div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="w-8 h-8 text-slate-500 group-hover:text-indigo-400 mx-auto transition-colors" />
                      <div className="text-xs text-slate-300 font-medium">
                        Click to browse or drag file here
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Max file size: 25MB • Formats: .pdf, .md, .txt, .docx
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Project Scope Assignment */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Assign to Project (Optional)
                </label>
                <select
                  value={uploadProjectId}
                  onChange={(e) => setUploadProjectId(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Workspace-wide (Available to all projects)</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      Project: {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                <span>
                  Uploaded files are automatically extracted, structure-chunked, embedded, and indexed for Hybrid RAG search in the background.
                </span>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || uploading}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 disabled:opacity-50 shadow-md shadow-indigo-900/30 transition-all"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Uploading & Queuing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-3.5 h-3.5" />
                      Start Ingestion
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspect Chunks Modal */}
      {inspectDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="relative w-full max-w-3xl max-h-[85vh] bg-slate-900 border border-slate-800 rounded-2xl flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                    {inspectDoc.filename}
                    <span className="text-[11px] font-mono font-normal text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/20">
                      {chunks.length} Chunks
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Structure-aware chunks with preserved page boundaries & vector embeddings
                  </p>
                </div>
              </div>
              <button
                onClick={() => setInspectDoc(null)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chunks List */}
            <div className="p-5 overflow-y-auto space-y-4 flex-1">
              {loadingChunks ? (
                <div className="flex flex-col items-center justify-center py-16 space-y-2">
                  <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                  <span className="text-xs text-slate-400">Loading indexed chunks...</span>
                </div>
              ) : chunks.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate-500">
                  No chunks found for this document.
                </div>
              ) : (
                chunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2.5"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-2 font-mono text-indigo-300 font-semibold">
                        <span className="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">
                          Chunk #{chunk.chunk_index}
                        </span>
                        {chunk.page_number && (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            Page {chunk.page_number}
                          </span>
                        )}
                      </div>
                      <div className="text-slate-500 font-mono text-[10px]">
                        ~{chunk.token_count} tokens
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-850 text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                      {chunk.content}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex justify-end shrink-0">
              <button
                onClick={() => setInspectDoc(null)}
                className="px-4 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

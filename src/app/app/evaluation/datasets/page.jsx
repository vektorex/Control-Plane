"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Database,
  Plus,
  Search,
  Upload,
  Download,
  Archive,
  RefreshCw,
  FolderOpen,
  CheckCircle2,
  AlertCircle,
  FileText,
  Lock,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function DatasetsListPage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Create Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({ name: "", description: "", initial_notes: "" });
  const [creating, setCreating] = useState(false);

  // Import Modal state
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [importFormat, setImportFormat] = useState("json");
  const [importContent, setImportContent] = useState("");
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState(null);

  useEffect(() => {
    loadDatasets();
  }, [statusFilter]);

  async function loadDatasets() {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluationLabService.listDatasets({
        status: statusFilter === "all" ? null : statusFilter,
      });
      setDatasets(res?.items || []);
    } catch (err) {
      setError(err?.message || "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!createForm.name.trim()) return;
    setCreating(true);
    try {
      await evaluationLabService.createDataset({
        name: createForm.name.trim(),
        description: createForm.description.trim() || undefined,
        initial_version_description: createForm.initial_notes.trim() || undefined,
      });
      setShowCreateModal(false);
      setCreateForm({ name: "", description: "", initial_notes: "" });
      await loadDatasets();
    } catch (err) {
      alert(err?.message || "Failed to create dataset");
    } finally {
      setCreating(false);
    }
  }

  async function handleImport(e) {
    e.preventDefault();
    if (!selectedDatasetId || !importContent.trim()) return;
    setImporting(true);
    setImportMessage(null);
    try {
      const res = await evaluationLabService.importCases(selectedDatasetId, {
        fileFormat: importFormat,
        content: importContent,
      });
      setImportMessage(`Successfully imported ${res.imported_count} cases (${res.skipped_count} skipped duplicates)`);
      setImportContent("");
      await loadDatasets();
      setTimeout(() => {
        setShowImportModal(false);
        setImportMessage(null);
      }, 1500);
    } catch (err) {
      setImportMessage(`Error: ${err?.message || "Import failed"}`);
    } finally {
      setImporting(false);
    }
  }

  const filteredDatasets = datasets.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase()) ||
    (d.description && d.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            <Link href="/app/evaluation" className="hover:text-foreground">Evaluation Lab</Link>
            <span>/</span>
            <span>Datasets</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-500" />
            Evaluation Datasets
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Manage test datasets, versioned evaluation cases, and benchmark baselines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (datasets.length > 0) setSelectedDatasetId(datasets[0].id);
              setShowImportModal(true);
            }}
            className="px-3 py-2 text-sm font-medium rounded-lg border border-border/60 hover:bg-accent/40 text-foreground transition flex items-center gap-1.5"
          >
            <Upload className="w-4 h-4 text-muted-foreground" />
            Import
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2 text-sm font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Dataset
          </button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search datasets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>

          <button
            onClick={loadDatasets}
            className="p-2 rounded-lg border border-border/60 hover:bg-accent/40 text-muted-foreground transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-primary" />
            Loading datasets...
          </div>
        ) : error ? (
          <div className="py-12 text-center text-sm text-red-500">{error}</div>
        ) : filteredDatasets.length === 0 ? (
          <div className="py-16 text-center text-sm text-muted-foreground space-y-2">
            <Database className="w-8 h-8 mx-auto text-muted-foreground/50" />
            <p>No evaluation datasets found.</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-xs text-primary hover:underline font-medium"
            >
              Create your first dataset
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border/40 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                <tr>
                  <th className="py-3 px-4">Dataset Name</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Updated</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {filteredDatasets.map((ds) => (
                  <tr key={ds.id} className="hover:bg-accent/20 transition">
                    <td className="py-3.5 px-4 font-medium text-foreground">
                      <Link
                        href={`/app/evaluation/datasets/${ds.id}`}
                        className="hover:text-primary transition flex items-center gap-2"
                      >
                        <Database className="w-4 h-4 text-blue-500/80" />
                        <div>
                          <span>{ds.name}</span>
                          {ds.description && (
                            <p className="text-xs text-muted-foreground font-normal line-clamp-1">{ds.description}</p>
                          )}
                        </div>
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 text-foreground font-mono text-xs">
                      v{ds.version}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-muted text-muted-foreground uppercase">
                        {ds.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-muted-foreground">
                      {new Date(ds.updated_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <Link
                        href={`/app/evaluation/datasets/${ds.id}`}
                        className="px-2.5 py-1 text-xs font-medium rounded border border-border/60 hover:bg-accent text-foreground transition"
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Dataset Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/70 rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-foreground">Create Evaluation Dataset</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Dataset Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Production QA Benchmark"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Purpose of this dataset..."
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Initial Version Notes</label>
                <input
                  type="text"
                  placeholder="e.g. v1 baseline test suite"
                  value={createForm.initial_notes}
                  onChange={(e) => setCreateForm({ ...createForm, initial_notes: e.target.value })}
                  className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 text-sm rounded-lg border border-border/60 hover:bg-accent text-foreground transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-1.5 text-sm font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Dataset"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/70 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
              <Upload className="w-5 h-5 text-primary" />
              Import Evaluation Cases
            </h2>

            <form onSubmit={handleImport} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Target Dataset</label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} (v{d.version})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Format</label>
                  <select
                    value={importFormat}
                    onChange={(e) => setImportFormat(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="json">JSON Array</option>
                    <option value="jsonl">JSON Lines (JSONL)</option>
                    <option value="csv">CSV (case_key, name, input)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Payload Limit</label>
                  <p className="text-xs text-muted-foreground mt-2">Max 10,000 cases / 50MB</p>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">File Content / Paste Data *</label>
                <textarea
                  rows={6}
                  required
                  placeholder={
                    importFormat === "json"
                      ? '[{"case_key": "q1", "name": "Test Q1", "input_data": {"input": "Hello"}}]'
                      : importFormat === "jsonl"
                      ? '{"case_key": "q1", "input_data": {"input": "Hello"}}\n{"case_key": "q2", "input_data": {"input": "World"}}'
                      : "case_key,name,input,expected_output\nq1,Q1,Hello,World"
                  }
                  value={importContent}
                  onChange={(e) => setImportContent(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-xs font-mono rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              {importMessage && (
                <div
                  className={`text-xs p-2.5 rounded-lg border ${
                    importMessage.startsWith("Error")
                      ? "bg-red-500/10 text-red-500 border-red-500/20"
                      : "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                  }`}
                >
                  {importMessage}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-3 py-1.5 text-sm rounded-lg border border-border/60 hover:bg-accent text-foreground transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={importing || !importContent.trim()}
                  className="px-4 py-1.5 text-sm font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition disabled:opacity-50"
                >
                  {importing ? "Importing..." : "Start Import"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

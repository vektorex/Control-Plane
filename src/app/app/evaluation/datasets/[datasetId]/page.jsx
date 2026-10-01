"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Database,
  Plus,
  Trash2,
  Edit,
  Download,
  Upload,
  Lock,
  RefreshCw,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Tag,
  ShieldCheck,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function DatasetDetailPage() {
  const params = useParams();
  const datasetId = params?.datasetId;

  const [dataset, setDataset] = useState(null);
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Version Modal
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [versionNotes, setVersionNotes] = useState("");
  const [cloneCases, setCloneCases] = useState(true);
  const [creatingVersion, setCreatingVersion] = useState(false);

  // Add/Edit Case Modal
  const [showCaseModal, setShowCaseModal] = useState(false);
  const [editingCaseId, setEditingCaseId] = useState(null);
  const [caseForm, setCaseForm] = useState({
    case_key: "",
    name: "",
    input_text: "",
    expected_output: "",
    assertion_type: "contains",
    assertion_val: "",
  });
  const [savingCase, setSavingCase] = useState(false);

  useEffect(() => {
    if (datasetId) {
      loadDatasetDetails();
    }
  }, [datasetId]);

  useEffect(() => {
    if (datasetId && selectedVersionId) {
      loadCases(selectedVersionId);
    }
  }, [selectedVersionId]);

  async function loadDatasetDetails() {
    setLoading(true);
    setError(null);
    try {
      const ds = await evaluationLabService.getDataset(datasetId);
      setDataset(ds);
      if (ds?.active_version_id) {
        setSelectedVersionId(ds.active_version_id);
      }
    } catch (err) {
      setError(err?.message || "Failed to load dataset");
    } finally {
      setLoading(false);
    }
  }

  async function loadCases(versionId) {
    try {
      const res = await evaluationLabService.listCases(datasetId, { versionId });
      setCases(res?.items || []);
    } catch (err) {
      console.error("Failed to load cases", err);
    }
  }

  async function handleCreateVersion(e) {
    e.preventDefault();
    setCreatingVersion(true);
    try {
      const newV = await evaluationLabService.createDatasetVersion(datasetId, {
        description: versionNotes.trim() || undefined,
        clone_from_version_id: cloneCases ? selectedVersionId : undefined,
      });
      setShowVersionModal(false);
      setVersionNotes("");
      await loadDatasetDetails();
      setSelectedVersionId(newV.id);
    } catch (err) {
      alert(err?.message || "Failed to create new version");
    } finally {
      setCreatingVersion(false);
    }
  }

  async function handleSaveCase(e) {
    e.preventDefault();
    if (!caseForm.case_key.trim() || !caseForm.name.trim()) return;
    setSavingCase(true);

    const assertions = [];
    if (caseForm.assertion_val.trim()) {
      assertions.push({
        type: caseForm.assertion_type,
        value: caseForm.assertion_val.trim(),
        path: caseForm.assertion_type === "json_fields" ? undefined : "text",
        fields: caseForm.assertion_type === "json_fields" ? [caseForm.assertion_val.trim()] : undefined,
      });
    }

    const payload = {
      case_key: caseForm.case_key.trim(),
      name: caseForm.name.trim(),
      input_data: { input: caseForm.input_text.trim() },
      expected_output: caseForm.expected_output.trim() || undefined,
      assertions,
    };

    try {
      if (editingCaseId) {
        await evaluationLabService.updateCase(editingCaseId, payload);
      } else {
        await evaluationLabService.createCase(datasetId, payload, selectedVersionId);
      }
      setShowCaseModal(false);
      setEditingCaseId(null);
      setCaseForm({
        case_key: "",
        name: "",
        input_text: "",
        expected_output: "",
        assertion_type: "contains",
        assertion_val: "",
      });
      await loadCases(selectedVersionId);
    } catch (err) {
      alert(err?.message || "Failed to save evaluation case");
    } finally {
      setSavingCase(false);
    }
  }

  async function handleDeleteCase(caseId) {
    if (!confirm("Are you sure you want to delete this evaluation case?")) return;
    try {
      await evaluationLabService.deleteCase(caseId);
      await loadCases(selectedVersionId);
    } catch (err) {
      alert(err?.message || "Failed to delete case");
    }
  }

  async function handleExport(format = "json") {
    try {
      const dataStr = await evaluationLabService.exportCases(datasetId, format, selectedVersionId);
      const blob = new Blob([dataStr], { type: format === "json" ? "application/json" : "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${dataset.name.toLowerCase().replace(/\s+/g, "_")}_v${dataset.version}.${format}`;
      a.click();
    } catch (err) {
      alert(err?.message || "Export failed");
    }
  }

  if (loading) {
    return (
      <div className="py-20 text-center text-sm text-muted-foreground flex flex-col items-center gap-2">
        <RefreshCw className="w-5 h-5 animate-spin text-primary" />
        Loading dataset details...
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center space-y-4">
        <p className="text-red-500">{error || "Dataset not found"}</p>
        <Link href="/app/evaluation/datasets" className="text-xs text-primary hover:underline">
          Return to Datasets
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            <Link href="/app/evaluation" className="hover:text-foreground">Evaluation Lab</Link>
            <span>/</span>
            <Link href="/app/evaluation/datasets" className="hover:text-foreground">Datasets</Link>
            <span>/</span>
            <span>{dataset.name}</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Database className="w-6 h-6 text-blue-500" />
              {dataset.name}
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-muted text-muted-foreground uppercase">
              {dataset.status}
            </span>
          </div>
          {dataset.description && (
            <p className="text-sm text-muted-foreground mt-1 max-w-2xl">{dataset.description}</p>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => handleExport("json")}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-accent/40 text-foreground transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-muted-foreground" />
            Export JSON
          </button>
          <button
            onClick={() => setShowVersionModal(true)}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border/60 hover:bg-accent/40 text-foreground transition flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            New Version
          </button>
          <button
            onClick={() => {
              setEditingCaseId(null);
              setCaseForm({
                case_key: `case_${cases.length + 1}`,
                name: "",
                input_text: "",
                expected_output: "",
                assertion_type: "contains",
                assertion_val: "",
              });
              setShowCaseModal(true);
            }}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Case
          </button>
        </div>
      </div>

      {/* Version Selector Bar */}
      <div className="flex items-center justify-between p-3.5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Active Version:
          </span>
          <span className="px-2.5 py-1 rounded bg-primary/10 text-primary border border-primary/20 text-xs font-mono font-bold">
            v{dataset.version}
          </span>
          <span className="text-xs text-muted-foreground">
            {cases.length} evaluation {cases.length === 1 ? "case" : "cases"}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Historical versions remain immutable once executed by an experiment.</span>
        </div>
      </div>

      {/* Cases Table */}
      <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-border/40 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <FileCode className="w-4 h-4 text-primary" />
            Evaluation Cases ({cases.length})
          </h2>
        </div>

        {cases.length === 0 ? (
          <div className="py-16 text-center text-sm text-muted-foreground space-y-2">
            <p>No evaluation cases in this dataset version yet.</p>
            <button
              onClick={() => {
                setEditingCaseId(null);
                setCaseForm({
                  case_key: "case_1",
                  name: "",
                  input_text: "",
                  expected_output: "",
                  assertion_type: "contains",
                  assertion_val: "",
                });
                setShowCaseModal(true);
              }}
              className="text-xs text-primary hover:underline font-medium"
            >
              Add your first evaluation case
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border/40 text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                <tr>
                  <th className="py-3 px-4">Key</th>
                  <th className="py-3 px-4">Case Name</th>
                  <th className="py-3 px-4">Input Prompt / Data</th>
                  <th className="py-3 px-4">Expected Output</th>
                  <th className="py-3 px-4">Assertions</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-accent/20 transition">
                    <td className="py-3 px-4 font-mono text-xs text-foreground font-medium">
                      {c.case_key}
                    </td>
                    <td className="py-3 px-4 text-foreground font-medium">
                      {c.name}
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground max-w-xs truncate font-mono">
                      {typeof c.input_data === "object" ? JSON.stringify(c.input_data) : String(c.input_data)}
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground max-w-xs truncate">
                      {c.expected_output || "—"}
                    </td>
                    <td className="py-3 px-4">
                      {c.assertions && c.assertions.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {c.assertions.map((a, i) => (
                            <span
                              key={i}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 border border-blue-500/20 font-mono"
                            >
                              {a.type}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">0 rules</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right space-x-1">
                      <button
                        onClick={() => {
                          setEditingCaseId(c.id);
                          setCaseForm({
                            case_key: c.case_key,
                            name: c.name,
                            input_text: c.input_data?.input || JSON.stringify(c.input_data),
                            expected_output: c.expected_output || "",
                            assertion_type: c.assertions?.[0]?.type || "contains",
                            assertion_val: c.assertions?.[0]?.value || "",
                          });
                          setShowCaseModal(true);
                        }}
                        className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition"
                        title="Edit case"
                      >
                        <Edit className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteCase(c.id)}
                        className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-red-500 transition"
                        title="Delete case"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Case Modal */}
      {showCaseModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/70 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-foreground">
              {editingCaseId ? "Edit Evaluation Case" : "Add Evaluation Case"}
            </h2>

            <form onSubmit={handleSaveCase} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Case Key *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. test_case_01"
                    value={caseForm.case_key}
                    onChange={(e) => setCaseForm({ ...caseForm, case_key: e.target.value })}
                    className="w-full mt-1 px-3 py-1.5 text-xs font-mono rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Arithmetic question"
                    value={caseForm.name}
                    onChange={(e) => setCaseForm({ ...caseForm, name: e.target.value })}
                    className="w-full mt-1 px-3 py-1.5 text-xs rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Input Prompt / Instructions *</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Input text passed to model/task during evaluation..."
                  value={caseForm.input_text}
                  onChange={(e) => setCaseForm({ ...caseForm, input_text: e.target.value })}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Expected Output (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Gold standard response text..."
                  value={caseForm.expected_output}
                  onChange={(e) => setCaseForm({ ...caseForm, expected_output: e.target.value })}
                  className="w-full mt-1 px-3 py-2 text-xs rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              {/* Assertion Builder */}
              <div className="p-3 rounded-lg border border-border/50 bg-muted/20 space-y-2">
                <span className="text-xs font-semibold text-foreground">Deterministic Assertion Rule</span>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-muted-foreground">Rule Type</label>
                    <select
                      value={caseForm.assertion_type}
                      onChange={(e) => setCaseForm({ ...caseForm, assertion_type: e.target.value })}
                      className="w-full mt-0.5 px-2 py-1 text-xs rounded border border-border/60 bg-background/50"
                    >
                      <option value="contains">contains (substring)</option>
                      <option value="not_contains">not_contains</option>
                      <option value="exact_match">exact_match</option>
                      <option value="regex">regex (pattern)</option>
                      <option value="json_fields">json_fields (required key)</option>
                      <option value="citation_exists">citation_exists</option>
                      <option value="grounded_claims">grounded_claims</option>
                      <option value="required_fields">required_fields</option>
                      <option value="output_format">output_format</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-muted-foreground">Expected Value / Pattern</label>
                    <input
                      type="text"
                      placeholder="e.g. 42 or postgresql"
                      value={caseForm.assertion_val}
                      onChange={(e) => setCaseForm({ ...caseForm, assertion_val: e.target.value })}
                      className="w-full mt-0.5 px-2 py-1 text-xs rounded border border-border/60 bg-background/50 font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
                <button
                  type="button"
                  onClick={() => setShowCaseModal(false)}
                  className="px-3 py-1.5 text-xs rounded-lg border border-border/60 hover:bg-accent text-foreground transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingCase}
                  className="px-4 py-1.5 text-xs font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition disabled:opacity-50"
                >
                  {savingCase ? "Saving..." : editingCaseId ? "Update Case" : "Add Case"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Version Modal */}
      {showVersionModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/70 rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h2 className="text-lg font-bold text-foreground">Create New Dataset Version</h2>
            <p className="text-xs text-muted-foreground">
              Creating a new immutable version lets you modify or add cases without affecting past experiment results.
            </p>

            <form onSubmit={handleCreateVersion} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Version Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Added edge-case prompts for math"
                  value={versionNotes}
                  onChange={(e) => setVersionNotes(e.target.value)}
                  className="w-full mt-1 px-3 py-1.5 text-xs rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="cloneCases"
                  checked={cloneCases}
                  onChange={(e) => setCloneCases(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary"
                />
                <label htmlFor="cloneCases" className="text-xs text-foreground font-medium">
                  Copy existing {cases.length} cases into the new version
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
                <button
                  type="button"
                  onClick={() => setShowVersionModal(false)}
                  className="px-3 py-1.5 text-xs rounded-lg border border-border/60 hover:bg-accent text-foreground transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingVersion}
                  className="px-4 py-1.5 text-xs font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground transition disabled:opacity-50"
                >
                  {creatingVersion ? "Creating..." : "Create Version"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

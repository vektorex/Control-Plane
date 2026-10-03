"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  FileCode2,
  ArrowLeft,
  GitBranch,
  ShieldCheck,
  FlaskConical,
  Play,
  RotateCcw,
  Plus,
  Eye,
  CheckCircle2,
  AlertTriangle,
  History,
  Lock,
  Layers,
  Sparkles,
  TrendingUp,
  Cpu,
  Hash,
  Send,
  Sliders,
  Check,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import { promptService } from "@/services/prompts";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";

export default function PromptHubPage({ params }) {
  const unwrappedParams = use(params);
  const promptId = unwrappedParams.promptId;
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") || "editor";

  const [activeTab, setActiveTab] = useState(initialTab);
  const [prompt, setPrompt] = useState(null);
  const [versions, setVersions] = useState([]);
  const [releases, setReleases] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Editor State
  const [selectedVersionId, setSelectedVersionId] = useState(null);
  const [editorContent, setEditorContent] = useState("");
  const [editorSchema, setEditorSchema] = useState("{}");
  const [editorConfig, setEditorConfig] = useState("{}");
  const [variableInputs, setVariableInputs] = useState({});
  const [previewResult, setPreviewResult] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testModel, setTestModel] = useState("gpt-4o-mini");

  // Save Version Modal
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveSummary, setSaveSummary] = useState("");
  const [savingVersion, setSavingVersion] = useState(false);

  // Diff State
  const [baseVerId, setBaseVerId] = useState("");
  const [targetVerId, setTargetVerId] = useState("");
  const [diffResult, setDiffResult] = useState(null);
  const [diffLoading, setDiffLoading] = useState(false);

  // Release & Rollback Modal State
  const [showPromoteModal, setShowPromoteModal] = useState(false);
  const [promoteEnv, setPromoteEnv] = useState("staging");
  const [promoteVerId, setPromoteVerId] = useState("");
  const [promoting, setPromoting] = useState(false);

  const [showRollbackModal, setShowRollbackModal] = useState(false);
  const [rollbackEnv, setRollbackEnv] = useState("production");
  const [rollbackVerId, setRollbackVerId] = useState("");
  const [rollbackReason, setRollbackReason] = useState("");
  const [rollingBack, setRollingBack] = useState(false);

  // Experiment Modal State
  const [showExpModal, setShowExpModal] = useState(false);
  const [expName, setExpName] = useState("");
  const [expKey, setExpKey] = useState("task_id");
  const [expVariants, setExpVariants] = useState([
    { label: "A", prompt_version_id: "", allocation_weight: 50 },
    { label: "B", prompt_version_id: "", allocation_weight: 50 },
  ]);
  const [creatingExp, setCreatingExp] = useState(false);
  const [selectedExpResults, setSelectedExpResults] = useState(null);

  // Fetch all core prompt details
  const fetchAllData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [promptRes, verRes, relRes, expRes] = await Promise.all([
        promptService.getPrompt(promptId),
        promptService.listVersions(promptId),
        promptService.listReleases(promptId),
        promptService.listExperiments({ prompt_id: promptId }),
      ]);

      setPrompt(promptRes);
      setVersions(verRes || []);
      setReleases(relRes || []);
      setExperiments(expRes || []);

      // If version not set yet, pick latest
      if (verRes && verRes.length > 0) {
        const latest = verRes[0];
        setSelectedVersionId((prev) => prev || latest.id);
        setEditorContent(latest.content || "");
        setEditorSchema(JSON.stringify(latest.variable_schema || {}, null, 2));
        setEditorConfig(JSON.stringify(latest.execution_config || {}, null, 2));

        // Prepopulate variable inputs from schema
        if (latest.variable_schema) {
          const initVars = {};
          Object.keys(latest.variable_schema).forEach((k) => {
            initVars[k] = `Sample ${k}`;
          });
          setVariableInputs(initVars);
        }

        // Set default diff versions if at least 2 versions
        if (verRes.length >= 2) {
          setBaseVerId(verRes[1].id);
          setTargetVerId(verRes[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load prompt data:", err);
      setError(err.message || "Failed to load prompt details");
    } finally {
      setLoading(false);
    }
  }, [promptId]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // When selected version changes
  const handleVersionChange = (verId) => {
    setSelectedVersionId(verId);
    const found = versions.find((v) => v.id === verId);
    if (found) {
      setEditorContent(found.content || "");
      setEditorSchema(JSON.stringify(found.variable_schema || {}, null, 2));
      setEditorConfig(JSON.stringify(found.execution_config || {}, null, 2));
      setPreviewResult(null);
      setTestResult(null);

      if (found.variable_schema) {
        const initVars = {};
        Object.keys(found.variable_schema).forEach((k) => {
          initVars[k] = variableInputs[k] || `Sample ${k}`;
        });
        setVariableInputs(initVars);
      }
    }
  };

  // Preview Prompt Rendering (Deterministic, no LLM call)
  const handlePreview = async () => {
    try {
      setPreviewLoading(true);
      const res = await promptService.previewPrompt(promptId, {
        version_id: selectedVersionId,
        content: editorContent,
        variable_schema: editorSchema ? JSON.parse(editorSchema) : {},
        variables: variableInputs,
      });
      setPreviewResult(res);
    } catch (err) {
      alert(`Preview Error: ${err.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Test Run via AI Gateway
  const handleTestRun = async () => {
    try {
      setTestLoading(true);
      setTestResult(null);
      const res = await promptService.testPrompt(promptId, {
        version_id: selectedVersionId,
        variables: variableInputs,
        model: testModel,
      });
      setTestResult(res);
    } catch (err) {
      alert(`Test Execution Error: ${err.message}`);
    } finally {
      setTestLoading(false);
    }
  };

  // Save as new version
  const handleSaveVersion = async () => {
    try {
      setSavingVersion(true);
      let parsedSchema = null;
      let parsedConfig = null;
      if (editorSchema.trim()) parsedSchema = JSON.parse(editorSchema);
      if (editorConfig.trim()) parsedConfig = JSON.parse(editorConfig);

      const newVer = await promptService.createVersion(promptId, {
        content: editorContent,
        variable_schema: parsedSchema,
        execution_config: parsedConfig,
        change_summary: saveSummary.trim() || "Updated prompt iteration",
      });

      setShowSaveModal(false);
      setSaveSummary("");
      await fetchAllData();
      setSelectedVersionId(newVer.id);
    } catch (err) {
      alert(`Save Version Error: ${err.message}`);
    } finally {
      setSavingVersion(false);
    }
  };

  // Publish draft version
  const handlePublish = async (verId) => {
    if (!confirm("Are you sure you want to publish this version? Published versions are permanently immutable.")) {
      return;
    }
    try {
      await promptService.publishVersion(promptId, verId);
      await fetchAllData();
    } catch (err) {
      alert(`Publish Error: ${err.message}`);
    }
  };

  // Compare diff
  const handleCompareDiff = async () => {
    if (!baseVerId || !targetVerId) return;
    try {
      setDiffLoading(true);
      const res = await promptService.compareVersions(promptId, baseVerId, targetVerId);
      setDiffResult(res);
    } catch (err) {
      alert(`Diff Error: ${err.message}`);
    } finally {
      setDiffLoading(false);
    }
  };

  // Promote Release
  const handlePromoteRelease = async () => {
    try {
      setPromoting(true);
      await promptService.createRelease(promptId, {
        environment: promoteEnv,
        version_id: promoteVerId,
      });
      setShowPromoteModal(false);
      await fetchAllData();
    } catch (err) {
      alert(`Promotion Failed: ${err.message}`);
    } finally {
      setPromoting(false);
    }
  };

  // Rollback Release
  const handleRollbackRelease = async () => {
    try {
      setRollingBack(true);
      await promptService.rollbackRelease(promptId, {
        environment: rollbackEnv,
        target_version_id: rollbackVerId || null,
        rollback_reason: rollbackReason.trim() || "Manual rollback requested",
      });
      setShowRollbackModal(false);
      setRollbackReason("");
      await fetchAllData();
    } catch (err) {
      alert(`Rollback Failed: ${err.message}`);
    } finally {
      setRollingBack(false);
    }
  };

  // Create Experiment
  const handleCreateExperiment = async () => {
    try {
      setCreatingExp(true);
      const exp = await promptService.createExperiment({
        prompt_id: promptId,
        name: expName.trim() || `Experiment ${prompt?.key}`,
        allocation_key: expKey,
        variants: expVariants.map((v) => ({
          label: v.label,
          prompt_version_id: v.prompt_version_id,
          allocation_weight: Number(v.allocation_weight) || 50,
        })),
      });
      setShowExpModal(false);
      setExpName("");
      await fetchAllData();
    } catch (err) {
      alert(`Experiment creation error: ${err.message}`);
    } finally {
      setCreatingExp(false);
    }
  };

  // View Experiment Results
  const handleViewExpResults = async (expId) => {
    try {
      const res = await promptService.getExperimentResults(expId);
      setSelectedExpResults(res);
    } catch (err) {
      alert(`Failed to load experiment results: ${err.message}`);
    }
  };

  const selectedVersion = versions.find((v) => v.id === selectedVersionId);
  const isPublished = selectedVersion?.status === "published";

  // Tab definitions
  const tabs = [
    { id: "editor", label: "Editor & Preview", icon: FileCode2 },
    { id: "versions", label: "Versions & Diff", icon: History, count: versions.length },
    { id: "releases", label: "Releases & Environments", icon: ShieldCheck, count: releases.length },
    { id: "experiments", label: "A/B Experiments", icon: FlaskConical, count: experiments.length },
  ];

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
        <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        Loading prompt asset hub...
      </div>
    );
  }

  if (error || !prompt) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-rose-400 text-sm">{error || "Prompt not found"}</p>
        <Link href="/app/prompts">
          <Button variant="outline" size="sm">
            Back to Registry
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Metadata */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/app/prompts"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white">{prompt.name}</h1>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-950 text-indigo-300 border border-slate-800">
                {prompt.key}
              </span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {prompt.prompt_type}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {prompt.description || "Governed AI prompt template asset."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick Release Status Pills */}
          <div className="flex items-center gap-1.5 text-xs bg-slate-950 p-1 rounded-lg border border-slate-800">
            <span className="px-2 py-0.5 rounded text-[11px] font-mono flex items-center gap-1.5 text-emerald-400 bg-emerald-950/40 border border-emerald-800/40">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Prod: {prompt.production_version ? `v${prompt.production_version.version_number}` : "None"}
            </span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono flex items-center gap-1.5 text-amber-400 bg-amber-950/40 border border-amber-800/40">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Staging: {prompt.staging_version ? `v${prompt.staging_version.version_number}` : "None"}
            </span>
          </div>

          <Button
            size="sm"
            onClick={() => {
              setPromoteVerId(selectedVersionId);
              setShowPromoteModal(true);
            }}
            className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            Promote Release
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* ========================================================================= */}
      {/* TAB 1: EDITOR & LIVE PREVIEW */}
      {/* ========================================================================= */}
      {activeTab === "editor" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Editor & Config (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {/* Version Bar */}
            <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Viewing Version:</span>
                <select
                  value={selectedVersionId || ""}
                  onChange={(e) => handleVersionChange(e.target.value)}
                  className="text-xs font-mono bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      v{v.version_number} ({v.status}) - {v.change_summary || "No summary"}
                    </option>
                  ))}
                </select>

                {isPublished && (
                  <span className="flex items-center gap-1 text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                    <Lock className="w-3 h-3" />
                    Immutable
                  </span>
                )}
                {selectedVersion?.status === "draft" && (
                  <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    Draft
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {selectedVersion?.status === "draft" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handlePublish(selectedVersion.id)}
                    className="text-xs text-emerald-400 border-emerald-800/50 hover:bg-emerald-950/40"
                  >
                    Publish v{selectedVersion.version_number}
                  </Button>
                )}
                <Button
                  size="sm"
                  onClick={() => setShowSaveModal(true)}
                  className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white"
                >
                  Save as New Version
                </Button>
              </div>
            </div>

            {/* Immutability Banner */}
            {isPublished && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-300 text-xs flex items-center gap-2">
                <Lock className="w-4 h-4 shrink-0 text-amber-400" />
                <span>
                  <strong>Published versions are immutable.</strong> You can freely edit this content; saving will automatically create a new draft iteration (e.g. v{versions.length + 1}).
                </span>
              </div>
            )}

            {/* Content Editor */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-200">
                  Prompt Template Content
                </label>
                <span className="text-[11px] font-mono text-slate-500">
                  {editorContent.length} chars
                </span>
              </div>
              <textarea
                rows={12}
                value={editorContent}
                onChange={(e) => setEditorContent(e.target.value)}
                className="w-full p-3 font-mono text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 resize-y"
                placeholder="Enter prompt with {{input.variable}} syntax..."
              />
            </div>

            {/* Variable Schema & Config Expander */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
              <h3 className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                Variable Schema & Execution Config
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">
                    Variable Schema (JSON)
                  </label>
                  <textarea
                    rows={4}
                    value={editorSchema}
                    onChange={(e) => setEditorSchema(e.target.value)}
                    className="w-full p-2 font-mono text-[11px] bg-slate-950 border border-slate-800 rounded text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">
                    Execution Config (JSON)
                  </label>
                  <textarea
                    rows={4}
                    value={editorConfig}
                    onChange={(e) => setEditorConfig(e.target.value)}
                    className="w-full p-2 font-mono text-[11px] bg-slate-950 border border-slate-800 rounded text-slate-200"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Variable Preview & AI Gateway Tester (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Variable Binding Inputs */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-emerald-400" />
                  Test Variable Inputs
                </h3>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handlePreview}
                  disabled={previewLoading}
                  className="text-xs text-slate-200"
                >
                  {previewLoading ? "Validating..." : "Preview Render"}
                </Button>
              </div>

              {Object.keys(variableInputs).length === 0 ? (
                <div className="text-[11px] text-slate-500 py-3 text-center border border-dashed border-slate-800 rounded-lg">
                  No schema variables specified. You can add one below:
                  <div className="mt-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        setVariableInputs((prev) => ({
                          ...prev,
                          "input.topic": "Distributed Consensus Systems",
                        }))
                      }
                      className="text-[10px]"
                    >
                      + Add input.topic
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {Object.entries(variableInputs).map(([key, val]) => (
                    <div key={key}>
                      <label className="block text-[11px] font-mono text-slate-400 mb-0.5">
                        {key}
                      </label>
                      <input
                        type="text"
                        value={val}
                        onChange={(e) =>
                          setVariableInputs((prev) => ({
                            ...prev,
                            [key]: e.target.value,
                          }))
                        }
                        className="w-full px-2.5 py-1 text-xs bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Preview Output */}
            {previewResult && (
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-semibold text-emerald-400">
                      Validated Deterministic Render
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    ~{previewResult.estimated_tokens} tokens
                  </span>
                </div>

                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-200 whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {previewResult.rendered_content}
                </div>

                <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between">
                  <span>Hash: {previewResult.content_hash?.substring(0, 16)}...</span>
                  <span>Vars Used: {previewResult.variables_used?.length || 0}</span>
                </div>

                {/* AI Gateway Test Button */}
                <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-2">
                  <select
                    value={testModel}
                    onChange={(e) => setTestModel(e.target.value)}
                    className="text-xs bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200"
                  >
                    <option value="gpt-4o-mini">gpt-4o-mini</option>
                    <option value="gpt-4o">gpt-4o</option>
                    <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                  </select>

                  <Button
                    size="sm"
                    onClick={handleTestRun}
                    disabled={testLoading}
                    className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    {testLoading ? "Executing via Gateway..." : "Run AI Gateway Test"}
                  </Button>
                </div>
              </div>
            )}

            {/* Test Run Execution Result */}
            {testResult && (
              <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Gateway Execution Success
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {testResult.latency_ms}ms · {testResult.total_tokens} tokens
                  </span>
                </div>
                <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-[11px] text-slate-200 whitespace-pre-wrap max-h-56 overflow-y-auto">
                  {testResult.response_content}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                  Model: {testResult.model} ({testResult.provider})
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: VERSIONS & DIFF */}
      {/* ========================================================================= */}
      {activeTab === "versions" && (
        <div className="space-y-6">
          {/* Versions Table */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" />
              Immutable Version History
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-400">
                <thead className="bg-slate-950 border-b border-slate-800 uppercase text-[10px] tracking-wider text-slate-400">
                  <tr>
                    <th className="py-2.5 px-3">Version</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Summary</th>
                    <th className="py-2.5 px-3">Created</th>
                    <th className="py-2.5 px-3">Published</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {versions.map((v) => (
                    <tr key={v.id} className="hover:bg-slate-850/30">
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-200">
                        v{v.version_number}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                            v.status === "published"
                              ? "bg-indigo-950 text-indigo-300 border border-indigo-800"
                              : v.status === "draft"
                              ? "bg-slate-800 text-slate-400 border border-slate-700"
                              : "bg-rose-950 text-rose-300 border border-rose-800"
                          }`}
                        >
                          {v.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {v.change_summary || "—"}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {new Date(v.created_at).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {v.published_at ? new Date(v.published_at).toLocaleString() : "—"}
                      </td>
                      <td className="py-2.5 px-3 text-right space-x-2">
                        {v.status === "draft" && (
                          <button
                            onClick={() => handlePublish(v.id)}
                            className="text-emerald-400 hover:text-emerald-300 font-medium"
                          >
                            Publish
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setSelectedVersionId(v.id);
                            setActiveTab("editor");
                          }}
                          className="text-indigo-400 hover:text-indigo-300 font-medium"
                        >
                          Load in Editor
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Side-by-side / Unified Diff Comparator */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-amber-400" />
              Compare Versions (Diff)
            </h2>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Base Version:</span>
                <select
                  value={baseVerId}
                  onChange={(e) => setBaseVerId(e.target.value)}
                  className="text-xs font-mono bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200"
                >
                  <option value="">Select version...</option>
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      v{v.version_number} ({v.status})
                    </option>
                  ))}
                </select>
              </div>

              <span className="text-slate-500 font-mono">→</span>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Target Version:</span>
                <select
                  value={targetVerId}
                  onChange={(e) => setTargetVerId(e.target.value)}
                  className="text-xs font-mono bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200"
                >
                  <option value="">Select version...</option>
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      v{v.version_number} ({v.status})
                    </option>
                  ))}
                </select>
              </div>

              <Button
                size="sm"
                onClick={handleCompareDiff}
                disabled={diffLoading || !baseVerId || !targetVerId}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-white"
              >
                {diffLoading ? "Comparing..." : "Compare Diff"}
              </Button>
            </div>

            {diffResult && (
              <div className="space-y-4 pt-2">
                <div className="flex items-center gap-4 text-xs font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-emerald-400">+{diffResult.added_lines} lines added</span>
                  <span className="text-rose-400">-{diffResult.removed_lines} lines removed</span>
                  <span className="text-slate-400">
                    Variables changed: {diffResult.variables_changed ? "Yes" : "No"}
                  </span>
                  <span className="text-slate-400">
                    Config changed: {diffResult.execution_config_changed ? "Yes" : "No"}
                  </span>
                </div>

                {/* Diff Viewer */}
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs overflow-x-auto max-h-96">
                  {diffResult.diff_lines?.map((line, idx) => {
                    const isAdd = line.startsWith("+") && !line.startsWith("+++");
                    const isRem = line.startsWith("-") && !line.startsWith("---");
                    const isHdr = line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++");
                    return (
                      <div
                        key={idx}
                        className={`py-0.5 px-2 rounded ${
                          isAdd
                            ? "bg-emerald-950/50 text-emerald-300"
                            : isRem
                            ? "bg-rose-950/50 text-rose-300"
                            : isHdr
                            ? "text-indigo-400 font-semibold"
                            : "text-slate-400"
                        }`}
                      >
                        {line}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: RELEASES & ENVIRONMENTS */}
      {/* ========================================================================= */}
      {activeTab === "releases" && (
        <div className="space-y-6">
          {/* Environments 3-Card Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Development */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                  Development
                </span>
                <span className="w-2 h-2 rounded-full bg-slate-400" />
              </div>
              <div className="space-y-1">
                <div className="text-xl font-bold font-mono text-slate-100">
                  {prompt.development_version ? `v${prompt.development_version.version_number}` : "Unassigned"}
                </div>
                <p className="text-[11px] text-slate-500">
                  Default target for local iteration and feature tests.
                </p>
              </div>
            </div>

            {/* Staging */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-semibold text-amber-400 tracking-wider">
                  Staging
                </span>
                <span className="w-2 h-2 rounded-full bg-amber-400" />
              </div>
              <div className="space-y-1">
                <div className="text-xl font-bold font-mono text-amber-400">
                  {prompt.staging_version ? `v${prompt.staging_version.version_number}` : "Unassigned"}
                </div>
                <p className="text-[11px] text-slate-500">
                  Pre-production validation and integration test target.
                </p>
              </div>
            </div>

            {/* Production */}
            <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/10 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-semibold text-emerald-400 tracking-wider">
                  Production
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <div className="space-y-1">
                <div className="text-xl font-bold font-mono text-emerald-400">
                  {prompt.production_version ? `v${prompt.production_version.version_number}` : "None Released"}
                </div>
                <p className="text-[11px] text-slate-400">
                  Authoritative production release bound to live tasks and planners.
                </p>
              </div>
            </div>
          </div>

          {/* Release Actions Bar */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-slate-200">
                Governance & Promotion Controls
              </h3>
              <p className="text-[11px] text-slate-400">
                Promote tested published versions or execute immediate rollback to a previous state.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRollbackModal(true)}
                className="text-xs text-rose-400 border-rose-800/40 hover:bg-rose-950/30 flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Rollback Release
              </Button>
              <Button
                size="sm"
                onClick={() => setShowPromoteModal(true)}
                className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Promote Version
              </Button>
            </div>
          </div>

          {/* Release Audit History */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3">
            <h3 className="text-xs font-semibold text-slate-200">
              Release Audit Log
            </h3>
            {releases.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">
                No release transitions recorded yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-400">
                  <thead className="bg-slate-950 border-b border-slate-800 uppercase text-[10px] tracking-wider text-slate-400">
                    <tr>
                      <th className="py-2 px-3">Environment</th>
                      <th className="py-2 px-3">Version</th>
                      <th className="py-2 px-3">Previous</th>
                      <th className="py-2 px-3">Status</th>
                      <th className="py-2 px-3">Released At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {releases.map((r) => (
                      <tr key={r.id}>
                        <td className="py-2.5 px-3 font-semibold text-slate-200 capitalize">
                          {r.environment}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400">
                          v{r.version?.version_number || "—"}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-500">
                          {r.previous_version ? `v${r.previous_version.version_number}` : "None"}
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                              r.status === "active"
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : "bg-slate-800 text-slate-500 border border-slate-700"
                            }`}
                          >
                            {r.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">
                          {new Date(r.released_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: A/B EXPERIMENTS */}
      {/* ========================================================================= */}
      {activeTab === "experiments" && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-indigo-400" />
                Prompt A/B Experiments
              </h2>
              <p className="text-xs text-slate-400">
                Run controlled variant allocation across live tasks or Evaluation Lab datasets without subjective automated scoring.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => setShowExpModal(true)}
              className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              New Experiment
            </Button>
          </div>

          {/* Experiments List */}
          {experiments.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-slate-800 rounded-xl space-y-3">
              <FlaskConical className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-xs font-semibold text-slate-300">No active experiments</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Configure deterministic A/B variant testing between two published versions to observe factual metrics.
              </p>
              <Button size="sm" onClick={() => setShowExpModal(true)}>
                Create First Experiment
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {experiments.map((exp) => (
                <div
                  key={exp.id}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-100 text-xs">{exp.name}</span>
                        <span
                          className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-bold ${
                            exp.status === "running"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : exp.status === "paused"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : "bg-slate-800 text-slate-400 border border-slate-700"
                          }`}
                        >
                          {exp.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Allocation Key: <code className="font-mono text-slate-400">{exp.allocation_key}</code>
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {exp.status === "draft" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={async () => {
                            await promptService.startExperiment(exp.id);
                            await fetchAllData();
                          }}
                          className="text-xs text-emerald-400"
                        >
                          Start Experiment
                        </Button>
                      )}
                      {exp.status === "running" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={async () => {
                            await promptService.pauseExperiment(exp.id);
                            await fetchAllData();
                          }}
                          className="text-xs text-amber-400"
                        >
                          Pause
                        </Button>
                      )}
                      <Button
                        size="sm"
                        onClick={() => handleViewExpResults(exp.id)}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-white"
                      >
                        Inspect Metrics
                      </Button>
                    </div>
                  </div>

                  {/* Variants Pills */}
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400">Variants:</span>
                    {exp.variants?.map((v) => (
                      <div
                        key={v.id}
                        className="flex items-center gap-2 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs font-mono"
                      >
                        <span className="font-bold text-indigo-400">[{v.label}]</span>
                        <span className="text-slate-300">v{v.version?.version_number}</span>
                        <span className="text-slate-500">({v.allocation_weight}%)</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Factual Metrics Drawer / Inspector */}
          {selectedExpResults && (
            <div className="p-5 rounded-xl border border-indigo-500/30 bg-slate-900/60 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-xs font-semibold text-slate-100">
                    Factual Variant Results ({selectedExpResults.name})
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  Total Observations: {selectedExpResults.total_observations}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-400">
                  <thead className="bg-slate-950 border-b border-slate-800 uppercase text-[10px] tracking-wider text-slate-400">
                    <tr>
                      <th className="py-2.5 px-3">Variant</th>
                      <th className="py-2.5 px-3">Version</th>
                      <th className="py-2.5 px-3">Observations</th>
                      <th className="py-2.5 px-3">Avg Latency</th>
                      <th className="py-2.5 px-3">Avg Tokens</th>
                      <th className="py-2.5 px-3">Pass Rate</th>
                      <th className="py-2.5 px-3">Error Rate</th>
                      <th className="py-2.5 px-3 text-right">Human Promotion</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {selectedExpResults.variants?.map((v) => (
                      <tr key={v.variant_id} className="hover:bg-slate-850/30">
                        <td className="py-2.5 px-3 font-mono font-bold text-indigo-400">
                          {v.label}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-200">
                          v{v.version_number}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {v.observations}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {v.avg_latency_ms}ms
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {v.avg_tokens}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="text-emerald-400 font-semibold">
                            {(v.pass_rate * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={
                              v.error_rate > 0 ? "text-rose-400 font-semibold" : "text-slate-400"
                            }
                          >
                            {(v.error_rate * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <Button
                            size="sm"
                            onClick={() => {
                              setPromoteVerId(v.prompt_version_id);
                              setShowPromoteModal(true);
                            }}
                            className="text-[11px] bg-indigo-600 hover:bg-indigo-500 text-white"
                          >
                            Release v{v.version_number}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: Save New Version */}
      {/* ========================================================================= */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Plus className="w-4 h-4 text-indigo-400" />
              Save New Prompt Version (v{versions.length + 1})
            </h3>
            <p className="text-xs text-slate-400">
              This will create a new draft version. Monotonic version numbering is automatically managed transactionally.
            </p>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Change Summary / Release Notes
              </label>
              <input
                type="text"
                placeholder="e.g. Refined chain-of-thought grounding and variable constraints"
                value={saveSummary}
                onChange={(e) => setSaveSummary(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSaveModal(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={savingVersion}
                onClick={handleSaveVersion}
                className="bg-indigo-600 hover:bg-indigo-500 text-white"
              >
                {savingVersion ? "Saving..." : "Create Draft"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: Promote Release */}
      {/* ========================================================================= */}
      {showPromoteModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Promote Prompt Release
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Target Environment
                </label>
                <select
                  value={promoteEnv}
                  onChange={(e) => setPromoteEnv(e.target.value)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="staging">Staging</option>
                  <option value="production">Production</option>
                  <option value="development">Development</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Published Version
                </label>
                <select
                  value={promoteVerId}
                  onChange={(e) => setPromoteVerId(e.target.value)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                >
                  <option value="">Select version...</option>
                  {versions
                    .filter((v) => v.status === "published")
                    .map((v) => (
                      <option key={v.id} value={v.id}>
                        v{v.version_number} - {v.change_summary || "Published"}
                      </option>
                    ))}
                </select>
              </div>

              {promoteEnv === "production" && (
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-300 text-[11px] flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 shrink-0 text-indigo-400" />
                  <span>
                    Promoting to production updates live application resolvers. Autonomous AI promotion is prohibited; this action will be logged in the audit ledger.
                  </span>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPromoteModal(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={promoting || !promoteVerId}
                onClick={handlePromoteRelease}
                className="bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                {promoting ? "Promoting..." : `Release to ${promoteEnv}`}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: Rollback Release */}
      {/* ========================================================================= */}
      {showRollbackModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-semibold text-rose-400 flex items-center gap-2">
              <RotateCcw className="w-4 h-4 text-rose-400" />
              Rollback Release Transition
            </h3>
            <p className="text-xs text-slate-400">
              Rollback creates a safe, auditable release transition back to a prior published version without mutating historical records.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Environment
                </label>
                <select
                  value={rollbackEnv}
                  onChange={(e) => setRollbackEnv(e.target.value)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="development">Development</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Rollback Reason <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Formatting regression detected in live pipeline"
                  value={rollbackReason}
                  onChange={(e) => setRollbackReason(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-rose-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRollbackModal(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={rollingBack || !rollbackReason.trim()}
                onClick={handleRollbackRelease}
                className="bg-rose-600 hover:bg-rose-500 text-white"
              >
                {rollingBack ? "Rolling back..." : "Confirm Rollback"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: Create Experiment */}
      {/* ========================================================================= */}
      {showExpModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-5 space-y-4 shadow-xl">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-indigo-400" />
              Configure Controlled Prompt Experiment
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Experiment Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Grounding Chain of Thought v1 vs v2"
                  value={expName}
                  onChange={(e) => setExpName(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Sticky Allocation Key
                </label>
                <select
                  value={expKey}
                  onChange={(e) => setExpKey(e.target.value)}
                  className="w-full text-xs bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 font-mono"
                >
                  <option value="task_id">task_id (Task execution scoped)</option>
                  <option value="user_id">user_id (User sticky)</option>
                  <option value="workflow_run_id">workflow_run_id (Workflow run scoped)</option>
                </select>
              </div>

              <div className="space-y-2 pt-2">
                <label className="block text-xs font-semibold text-slate-300">
                  Neutral Variants & Allocation Weights
                </label>
                {expVariants.map((v, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="w-7 text-center font-bold text-xs text-indigo-400 font-mono">
                      {v.label}
                    </span>
                    <select
                      value={v.prompt_version_id}
                      onChange={(e) => {
                        const newVars = [...expVariants];
                        newVars[idx].prompt_version_id = e.target.value;
                        setExpVariants(newVars);
                      }}
                      className="flex-1 text-xs bg-slate-950 border border-slate-800 rounded p-1.5 text-slate-200 font-mono"
                    >
                      <option value="">Select published version...</option>
                      {versions
                        .filter((ver) => ver.status === "published")
                        .map((ver) => (
                          <option key={ver.id} value={ver.id}>
                            v{ver.version_number} - {ver.change_summary || "Published"}
                          </option>
                        ))}
                    </select>
                    <input
                      type="number"
                      value={v.allocation_weight}
                      onChange={(e) => {
                        const newVars = [...expVariants];
                        newVars[idx].allocation_weight = e.target.value;
                        setExpVariants(newVars);
                      }}
                      placeholder="Weight %"
                      className="w-20 text-xs bg-slate-950 border border-slate-800 rounded p-1.5 text-slate-200 font-mono text-center"
                    />
                    <span className="text-xs text-slate-500">%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowExpModal(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={creatingExp || expVariants.some((v) => !v.prompt_version_id)}
                onClick={handleCreateExperiment}
                className="bg-indigo-600 hover:bg-indigo-500 text-white"
              >
                {creatingExp ? "Creating..." : "Save Experiment"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

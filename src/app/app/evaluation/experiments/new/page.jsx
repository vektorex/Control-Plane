"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  PlayCircle,
  Database,
  Cpu,
  Layers,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  RefreshCw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function NewExperimentPage() {
  const router = useRouter();

  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [activeVersionId, setActiveVersionId] = useState("");
  const [caseCount, setCaseCount] = useState(0);
  const [loadingDatasets, setLoadingDatasets] = useState(true);

  // Form State
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetType, setTargetType] = useState("model");
  const [model, setModel] = useState("gpt-4o-mini");
  const [provider, setProvider] = useState("openai");
  const [temperature, setTemperature] = useState(0.0);
  const [promptTemplate, setPromptTemplate] = useState("Answer concisely and cite sources where relevant: {input}");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      const selectedDs = datasets.find((d) => d.id === selectedDatasetId);
      if (selectedDs) {
        setActiveVersionId(selectedDs.active_version_id || "");
        loadCaseCount(selectedDatasetId, selectedDs.active_version_id);
      }
    }
  }, [selectedDatasetId, datasets]);

  async function loadDatasets() {
    setLoadingDatasets(true);
    try {
      const res = await evaluationLabService.listDatasets({ limit: 100 });
      const items = res?.items || [];
      setDatasets(items);
      if (items.length > 0) {
        setSelectedDatasetId(items[0].id);
        setActiveVersionId(items[0].active_version_id || "");
        setName(`Eval ${items[0].name} (${new Date().toLocaleDateString()})`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDatasets(false);
    }
  }

  async function loadCaseCount(dsId, versionId) {
    try {
      const res = await evaluationLabService.listCases(dsId, { versionId, limit: 1000 });
      setCaseCount(res?.items?.length || 0);
    } catch (err) {
      setCaseCount(0);
    }
  }

  async function handleLaunch(e) {
    e.preventDefault();
    if (!name.trim() || !activeVersionId) return;

    setSubmitting(true);
    setError(null);

    const targetConfig = {
      model,
      provider,
      temperature: parseFloat(temperature),
    };

    if (targetType === "prompt") {
      targetConfig.template = promptTemplate;
    }

    try {
      // 1. Create Experiment
      const exp = await evaluationLabService.createExperiment({
        name: name.trim(),
        description: description.trim() || undefined,
        dataset_version_id: activeVersionId,
        target_type: targetType,
        target_configuration: targetConfig,
      });

      // 2. Trigger Run
      await evaluationLabService.runExperiment(exp.id);

      // 3. Navigate to Results
      router.push(`/app/evaluation/experiments/${exp.id}`);
    } catch (err) {
      setError(err?.message || "Failed to launch experiment");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="border-b border-border/40 pb-5">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
          <Link href="/app/evaluation" className="hover:text-foreground">Evaluation Lab</Link>
          <span>/</span>
          <span>New Experiment</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <PlayCircle className="w-6 h-6 text-purple-500" />
          Experiment Builder
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Configure a deterministic evaluation run against a model, prompt, or task configuration.
        </p>
      </div>

      <form onSubmit={handleLaunch} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Configuration (2 cols) */}
          <div className="md:col-span-2 space-y-5">
            {/* General Info */}
            <div className="p-5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-4">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Sliders className="w-4 h-4 text-primary" />
                Experiment Details
              </h2>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Experiment Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. gpt-4o-mini Grounding Benchmark"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Goals or context for this evaluation..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            {/* Dataset Selection */}
            <div className="p-5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-4">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-500" />
                Target Dataset
              </h2>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Select Evaluation Dataset</label>
                {loadingDatasets ? (
                  <div className="text-xs text-muted-foreground py-2">Loading datasets...</div>
                ) : datasets.length === 0 ? (
                  <div className="text-xs text-amber-500 py-2">
                    No datasets found. Please create a dataset first.
                  </div>
                ) : (
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
                )}
              </div>
            </div>

            {/* Target & Model Parameters */}
            <div className="p-5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-4">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-500" />
                Evaluation Target & Inference Parameters
              </h2>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Target Type</label>
                  <select
                    value={targetType}
                    onChange={(e) => setTargetType(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="model">Direct Model Inference</option>
                    <option value="prompt">Prompt Template</option>
                    <option value="task">Simulated Task Flow</option>
                    <option value="workflow">Workflow Execution</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-muted-foreground">Model</label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="gpt-4o-mini">gpt-4o-mini</option>
                    <option value="gpt-4o">gpt-4o</option>
                    <option value="mock-model-v1">mock-model-v1 (Test)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Provider</label>
                  <input
                    type="text"
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-sm rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Temperature ({temperature})</label>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    className="w-full mt-3"
                  />
                </div>
              </div>

              {targetType === "prompt" && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">
                    Prompt Template (use &#123;input&#125;)
                  </label>
                  <textarea
                    rows={3}
                    value={promptTemplate}
                    onChange={(e) => setPromptTemplate(e.target.value)}
                    className="w-full mt-1 px-3 py-2 text-xs font-mono rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Experiment Preview (1 col) */}
          <div className="space-y-4">
            <div className="p-5 rounded-xl border border-primary/20 bg-primary/5 space-y-4 sticky top-6">
              <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                Experiment Preview
              </h3>

              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-border/30">
                  <span className="text-muted-foreground">Evaluation Cases:</span>
                  <span className="font-semibold text-foreground font-mono">{caseCount} cases</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-border/30">
                  <span className="text-muted-foreground">Estimated Model Calls:</span>
                  <span className="font-semibold text-foreground font-mono">{caseCount} calls</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-border/30">
                  <span className="text-muted-foreground">Concurrency Limit:</span>
                  <span className="font-semibold text-foreground font-mono">5 workers</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-border/30">
                  <span className="text-muted-foreground">Verification Checks:</span>
                  <span className="font-semibold text-foreground">Grounding, Format, Safety</span>
                </div>

                <div className="flex justify-between py-1.5 border-b border-border/30">
                  <span className="text-muted-foreground">Side-effect Guard:</span>
                  <span className="font-semibold text-emerald-500">Dry-run (Protected)</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-background/80 border border-border/50 text-[11px] text-muted-foreground flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  Evaluations execute with side-effects isolated. Write and destructive operations will not mutate external systems.
                </span>
              </div>

              {error && (
                <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-500">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting || caseCount === 0}
                className="w-full py-2.5 px-4 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground font-medium text-sm transition shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Launching Experiment...
                  </>
                ) : (
                  <>
                    <PlayCircle className="w-4 h-4" />
                    Launch Experiment
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

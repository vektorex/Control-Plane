"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FlaskConical,
  Database,
  PlayCircle,
  GitCompare,
  AlertTriangle,
  Plus,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Clock,
  Coins,
  ShieldAlert,
  Search,
  RefreshCw,
} from "lucide-react";
import { evaluationLabService } from "@/services/evaluationLab";

export default function EvaluationLabHubPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [datasets, setDatasets] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [dsRes, expRes] = await Promise.all([
        evaluationLabService.listDatasets({ limit: 10 }),
        evaluationLabService.listExperiments({ limit: 10 }),
      ]);
      setDatasets(dsRes?.items || []);
      setExperiments(expRes?.items || []);
    } catch (err) {
      setError(err?.message || "Failed to load Evaluation Lab data");
    } finally {
      setLoading(false);
    }
  }

  const completedExps = experiments.filter((e) => e.status === "completed");

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
              <FlaskConical className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                AI Evaluation Lab
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Deterministic datasets, verifiable assertions, repeatable experiments, and factual regression detection.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/app/evaluation/datasets"
            className="px-3.5 py-2 text-sm font-medium rounded-lg border border-border/60 hover:bg-accent/40 text-foreground transition flex items-center gap-2"
          >
            <Database className="w-4 h-4 text-muted-foreground" />
            Manage Datasets
          </Link>
          <Link
            href="/app/evaluation/experiments/new"
            className="px-4 py-2 text-sm font-medium rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Experiment
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Evaluation Datasets</span>
            <Database className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">{datasets.length}</p>
          <p className="text-xs text-muted-foreground">Versioned test collections</p>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Experiments</span>
            <PlayCircle className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">{experiments.length}</p>
          <p className="text-xs text-muted-foreground">{completedExps.length} completed verification runs</p>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">A/B Comparisons</span>
            <GitCompare className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">Factual Diff</p>
          <p className="text-xs text-muted-foreground">Zero subjective scoring</p>
        </div>

        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Regression Guard</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-foreground">Thresholds</p>
          <p className="text-xs text-muted-foreground">5% failure, 25% latency/cost limit</p>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Link
          href="/app/evaluation/datasets"
          className="p-5 rounded-xl border border-border/60 bg-card/60 hover:bg-accent/40 transition group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
              <Database className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-semibold text-foreground">Datasets & Versions</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Curate test cases, configure expected outputs, and import JSON/JSONL/CSV files.
          </p>
        </Link>

        <Link
          href="/app/evaluation/experiments/new"
          className="p-5 rounded-xl border border-border/60 bg-card/60 hover:bg-accent/40 transition group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
              <PlayCircle className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-semibold text-foreground">Experiment Builder</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Preview model calls, estimate usage, and execute repeatable evaluations against tasks or models.
          </p>
        </Link>

        <Link
          href="/app/evaluation/compare"
          className="p-5 rounded-xl border border-border/60 bg-card/60 hover:bg-accent/40 transition group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
              <GitCompare className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-semibold text-foreground">Factual Comparison</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Side-by-side empirical differential analysis of cases, assertions, latency, and tokens.
          </p>
        </Link>

        <Link
          href="/app/evaluation/regressions"
          className="p-5 rounded-xl border border-border/60 bg-card/60 hover:bg-accent/40 transition group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-semibold text-foreground">Continuous Regressions</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Detect lost assertions, grounding failures, and latency spikes across experiment iterations.
          </p>
        </Link>
      </div>

      {/* Recent Experiments & Datasets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Experiments */}
        <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
              <PlayCircle className="w-4 h-4 text-primary" />
              Recent Experiments
            </h2>
            <Link
              href="/app/evaluation/experiments/new"
              className="text-xs font-medium text-primary hover:underline flex items-center gap-1"
            >
              New Experiment <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-sm text-muted-foreground">Loading experiments...</div>
          ) : experiments.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No evaluation experiments run yet.
            </div>
          ) : (
            <div className="divide-y divide-border/30">
              {experiments.map((exp) => (
                <div key={exp.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <Link
                      href={`/app/evaluation/experiments/${exp.id}`}
                      className="font-medium text-sm text-foreground hover:text-primary transition truncate block"
                    >
                      {exp.name}
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                      <span className="capitalize">{exp.target_type}</span>
                      <span>•</span>
                      <span>{new Date(exp.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        exp.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                          : exp.status === "running"
                          ? "bg-blue-500/10 text-blue-500 border border-blue-500/20 animate-pulse"
                          : exp.status === "failed"
                          ? "bg-red-500/10 text-red-500 border border-red-500/20"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {exp.status}
                    </span>
                    <Link
                      href={`/app/evaluation/experiments/${exp.id}`}
                      className="text-xs text-primary hover:underline"
                    >
                      Results
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Datasets */}
        <div className="rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-500" />
              Evaluation Datasets
            </h2>
            <Link
              href="/app/evaluation/datasets"
              className="text-xs font-medium text-primary hover:underline flex items-center gap-1"
            >
              View All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-sm text-muted-foreground">Loading datasets...</div>
          ) : datasets.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No evaluation datasets created yet.
            </div>
          ) : (
            <div className="divide-y divide-border/30">
              {datasets.map((ds) => (
                <div key={ds.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <Link
                      href={`/app/evaluation/datasets/${ds.id}`}
                      className="font-medium text-sm text-foreground hover:text-primary transition truncate block"
                    >
                      {ds.name}
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                      <span>Version v{ds.version}</span>
                      <span>•</span>
                      <span>Updated {new Date(ds.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-muted text-muted-foreground uppercase">
                      {ds.status}
                    </span>
                    <Link
                      href={`/app/evaluation/datasets/${ds.id}`}
                      className="text-xs text-primary hover:underline"
                    >
                      Open
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  RefreshCw,
  Trash2,
  Sparkles,
  Send,
  Layers,
  ShieldCheck,
  Network,
  Clock,
  CheckCircle2,
  XCircle,
  FileCode,
  Share2,
  Loader2,
  Info,
  AlertCircle,
} from "lucide-react";
import { artifactService } from "@/services/artifacts";
import { ArtifactViewer } from "@/components/features/artifacts/ArtifactViewer";
import { ArtifactEvidenceCard } from "@/components/features/artifacts/ArtifactEvidenceCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export default function ArtifactDetailPage() {
  const params = useParams();
  const router = useRouter();
  const artifactId = params?.artifactId;

  const [artifact, setArtifact] = useState(null);
  const [parts, setParts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Analysis State
  const [instruction, setInstruction] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);

  // Evidence and Viewer sync
  const [activeRegion, setActiveRegion] = useState(null);
  const [activeTimestamp, setActiveTimestamp] = useState(null);
  const [activePage, setActivePage] = useState(1);

  const loadData = useCallback(async () => {
    if (!artifactId) return;
    setLoading(true);
    setError(null);
    try {
      const art = await artifactService.getArtifact(artifactId);
      setArtifact(art);

      try {
        const pList = await artifactService.getArtifactParts(artifactId);
        setParts(Array.isArray(pList) ? pList : pList?.parts || []);
      } catch (partErr) {
        console.warn("Could not fetch parts:", partErr);
      }
    } catch (err) {
      console.error("Failed to load artifact details:", err);
      setError(err?.message || "Failed to load artifact details.");
    } finally {
      setLoading(false);
    }
  }, [artifactId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleProcess = async () => {
    if (!artifactId) return;
    try {
      await artifactService.processArtifact(artifactId);
      loadData();
    } catch (err) {
      alert("Extraction trigger failed: " + err.message);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Permanently delete this artifact?")) return;
    try {
      await artifactService.deleteArtifact(artifactId);
      router.push("/app/artifacts");
    } catch (err) {
      alert("Failed to delete artifact: " + err.message);
    }
  };

  const handleRunAnalysis = async (e) => {
    e.preventDefault();
    if (!instruction.trim() || analyzing) return;

    setAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const res = await artifactService.analyzeArtifact(artifactId, {
        instruction: instruction.trim(),
        mode: "auto",
      });
      setAnalysisResult(res);
    } catch (err) {
      setAnalysisError(err?.message || "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[500px] flex flex-col items-center justify-center text-zinc-500 text-xs gap-3">
        <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
        <p>Loading multimodal artifact context...</p>
      </div>
    );
  }

  if (error || !artifact) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <AlertCircle className="h-12 w-12 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-zinc-200">Artifact Not Found</h2>
        <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">{error || "The artifact does not exist or you lack permission to view it."}</p>
        <Link href="/app/artifacts">
          <Button variant="outline" size="sm" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back to Library
          </Button>
        </Link>
      </div>
    );
  }

  const meta = artifact.metadata || {};

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 py-6">
      {/* Back button and Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <Link href="/app/artifacts">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-zinc-400 hover:text-white">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-zinc-100">{artifact.filename}</h1>
              <Badge variant="outline" className="text-[11px] capitalize border-zinc-700">
                {artifact.artifact_type}
              </Badge>
              <Badge
                variant="secondary"
                className={`text-[10px] ${
                  artifact.status === "ready"
                    ? "text-emerald-400 border-emerald-800/60"
                    : "text-amber-400"
                }`}
              >
                {artifact.status}
              </Badge>
            </div>
            <p className="text-xs text-zinc-500 font-mono mt-0.5">
              ID: {artifact.id} | MIME: {artifact.mime_type} | Size: {((artifact.size_bytes || 0) / 1024).toFixed(1)} KB
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleProcess}
            className="text-zinc-300 border-zinc-700"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Re-Extract Parts
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            className="text-rose-400 hover:text-rose-300"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Main Grid: Left is Media Viewer, Right is Analysis & Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Multimodal Viewer & Parts (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <ArtifactViewer
            artifact={artifact}
            parts={parts}
            activeRegion={activeRegion}
            activeTimestamp={activeTimestamp}
            activePage={activePage}
            onSelectTimestamp={(ts) => setActiveTimestamp(ts)}
            onSelectPage={(p) => setActivePage(p)}
          />

          {/* Extracted Parts breakdown */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-zinc-300 flex items-center gap-2 uppercase tracking-wider">
                <Layers className="h-4 w-4 text-purple-400" />
                Normalized Artifact Parts ({parts.length})
              </h3>
              <Badge variant="outline" className="text-[10px] text-zinc-500 border-zinc-700">
                First-Class Context
              </Badge>
            </div>

            {parts.length > 0 ? (
              <div className="divide-y divide-zinc-800/80 max-h-60 overflow-y-auto pr-1">
                {parts.map((p, idx) => (
                  <div key={p.id || idx} className="py-2.5 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-zinc-500 text-[10px] w-6">#{idx + 1}</span>
                      <Badge variant="secondary" className="capitalize text-[10px]">
                        {p.part_type}
                      </Badge>
                      <span className="text-zinc-300 truncate max-w-xs font-mono text-[11px]">
                        {p.content_reference || p.text_content?.slice(0, 40) || `Part ${p.id.slice(0, 8)}`}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-zinc-500 text-[11px] font-mono">
                      {p.token_estimate != null && <span>~{p.token_estimate} tokens</span>}
                      <span>{p.content_hash?.slice(0, 8)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500 py-2">
                No normalized parts extracted yet. Click &ldquo;Re-Extract Parts&rdquo; to process this artifact.
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Interactive Multimodal Reasoning, Evidence & Metadata (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Multimodal Analysis Prompt Box */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-zinc-200 flex items-center gap-2 uppercase tracking-wider">
                <Sparkles className="h-4 w-4 text-purple-400" />
                Multimodal Reasoning
              </h3>
              <Badge variant="outline" className="text-[10px] text-purple-400 border-purple-800">
                Unified AI Gateway
              </Badge>
            </div>

            <form onSubmit={handleRunAnalysis} className="space-y-3">
              <textarea
                rows={3}
                placeholder={
                  artifact.artifact_type === "image"
                    ? "Ask a question about this diagram, screenshot, or image..."
                    : artifact.artifact_type === "audio"
                    ? "Summarize discussion, list action items from recording..."
                    : artifact.artifact_type === "spreadsheet"
                    ? "Analyze revenue trend, highlight anomalies..."
                    : "Ask about this multimodal artifact..."
                }
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-purple-600 transition-colors"
              />

              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500">
                  Routes through Model Router & capability resolver
                </span>
                <Button
                  type="submit"
                  size="sm"
                  disabled={!instruction.trim() || analyzing}
                  className="bg-purple-600 hover:bg-purple-500 text-white text-xs"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5 mr-1.5" />
                      Execute Analysis
                    </>
                  )}
                </Button>
              </div>
            </form>

            {/* Analysis Error */}
            {analysisError && (
              <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{analysisError}</span>
              </div>
            )}

            {/* Analysis Result */}
            {analysisResult && (
              <div className="bg-zinc-950 border border-purple-900/50 rounded-lg p-4 space-y-3 mt-4">
                <div className="flex items-center justify-between text-xs text-zinc-400 border-b border-zinc-800/80 pb-2">
                  <span className="text-purple-400 font-medium flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Model: {analysisResult.model_used}
                  </span>
                  <span className="font-mono text-[10px] text-zinc-500">
                    {Math.round(analysisResult.latency_ms || 0)}ms
                  </span>
                </div>

                <div className="prose prose-invert max-w-none text-xs leading-relaxed text-zinc-200 whitespace-pre-wrap">
                  {analysisResult.result}
                </div>

                {analysisResult.fallback_used && (
                  <div className="p-2 rounded bg-amber-950/30 border border-amber-800/50 text-[11px] text-amber-300">
                    Explicit Vision Fallback was applied (model lacks native image input).
                  </div>
                )}

                {/* Evidence citations */}
                {analysisResult.evidence && analysisResult.evidence.length > 0 && (
                  <div className="pt-2 border-t border-zinc-800 space-y-2">
                    <h5 className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
                      Grounded Evidence Citations ({analysisResult.evidence.length})
                    </h5>
                    <div className="space-y-2">
                      {analysisResult.evidence.map((ev, idx) => (
                        <ArtifactEvidenceCard
                          key={idx}
                          evidence={ev}
                          onJumpToTimestamp={(ts) => setActiveTimestamp(ts)}
                          onHighlightRegion={(r) => setActiveRegion(r)}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Artifact Intelligence Metadata card */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-3 text-xs">
            <h4 className="font-semibold text-zinc-300 flex items-center gap-2 uppercase tracking-wider text-[11px]">
              <Info className="h-4 w-4 text-blue-400" />
              Security & Provenance Context
            </h4>

            <div className="space-y-2 divide-y divide-zinc-800">
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-500">Tenant Org</span>
                <span className="text-zinc-300 font-mono text-[11px]">{artifact.organization_id}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-500">Workspace</span>
                <span className="text-zinc-300 font-mono text-[11px]">{artifact.workspace_id}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-500">Data Trust Level</span>
                <Badge variant="outline" className="text-amber-400 border-amber-800 text-[10px]">
                  external_untrusted
                </Badge>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-500">Content Hash (SHA-256)</span>
                <span className="text-zinc-400 font-mono text-[10px]">
                  {artifact.content_hash?.slice(0, 16)}...
                </span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-500">Storage Ref</span>
                <span className="text-zinc-400 font-mono text-[10px]">
                  {artifact.storage_reference?.slice(0, 24)}...
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

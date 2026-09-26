"use client";

import React, { useState, useEffect, useRef } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { orchestratorService } from "@/services/orchestrator";
import {
  Terminal,
  Play,
  Square,
  Sparkles,
  Cpu,
  Zap,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  Clock,
  Layers,
} from "lucide-react";

export default function PlaygroundPage() {
  const [models, setModels] = useState([]);
  const [providers, setProviders] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("You are an expert AI orchestrator assistant. Provide precise, well-structured, and concise responses.");
  const [userPrompt, setUserPrompt] = useState("Explain how a multi-provider LLM abstraction layer works in 3 bullet points.");
  const [temperature, setTemperature] = useState(0.7);
  const [enableStreaming, setEnableStreaming] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [output, setOutput] = useState("");
  const [tokenUsage, setTokenUsage] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);

  const abortControllerRef = useRef(null);
  const timerRef = useRef(null);

  const fetchModels = async () => {
    try {
      setError(null);
      const data = await orchestratorService.getModels();
      if (data?.models?.length > 0) {
        setModels(data.models);
        setProviders(data.providers || []);
        const defaultModel = data.models.find((m) => m.is_default) || data.models[0];
        setSelectedModel(defaultModel.id);
      }
    } catch (err) {
      console.error("[Playground] Failed to load models:", err);
      setError(`Backend unreachable (${err.message}). Ensure the FastAPI server is running on port 8000.`);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleCopy = () => {
    if (!output) return;
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsStreaming(false);
    setIsLoading(false);
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!userPrompt.trim() || !selectedModel) return;

    setError(null);
    setOutput("");
    setTokenUsage(null);
    setIsLoading(true);
    setElapsedMs(0);

    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 50);

    const messages = [];
    if (systemPrompt.trim()) {
      messages.push({ role: "system", content: systemPrompt.trim() });
    }
    messages.push({ role: "user", content: userPrompt.trim() });

    const payload = {
      model: selectedModel,
      messages,
      temperature: Number(temperature),
      stream: enableStreaming,
    };

    if (enableStreaming) {
      setIsStreaming(true);
      const controller = new AbortController();
      abortControllerRef.current = controller;

      let accumulatedText = "";
      await orchestratorService.generateStream(payload, {
        signal: controller.signal,
        onChunk: (chunk) => {
          setIsLoading(false);
          if (chunk.content) {
            accumulatedText += chunk.content;
            setOutput(accumulatedText);
          }
          if (chunk.usage) {
            setTokenUsage(chunk.usage);
          }
        },
        onError: (err) => {
          clearInterval(timerRef.current);
          setIsStreaming(false);
          setIsLoading(false);
          setError(err.message || "Failed to stream response from backend LLM provider.");
        },
        onComplete: () => {
          clearInterval(timerRef.current);
          setIsStreaming(false);
          setIsLoading(false);
        },
      });
    } else {
      try {
        const res = await orchestratorService.generate(payload);
        setOutput(res.content || "");
        if (res.usage) {
          setTokenUsage(res.usage);
        }
      } catch (err) {
        setError(err.message || "Failed to generate completion from LLM provider.");
      } finally {
        clearInterval(timerRef.current);
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-850">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              LLM Abstraction Playground
            </h1>
            <Badge variant="info" dot className="text-[11px] font-mono">
              Internal Dev Testbed
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Test multi-provider routing, real-time SSE token streaming, and usage telemetry directly against the backend.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={RefreshCw} onClick={fetchModels}>
            Refresh Models
          </Button>
        </div>
      </div>

      {/* Backend connection warning if any */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-rose-200">Execution Error</div>
            <div className="text-rose-300/90 leading-relaxed font-mono">{error}</div>
          </div>
        </div>
      )}

      {/* Main Grid: Controls vs Output */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Request Configuration */}
        <div className="lg:col-span-5 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span>Model & Parameters</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Model Selector */}
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">
                  Target LLM Model
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono cursor-pointer"
                >
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
                  {models.length === 0 && (
                    <option value="" disabled>
                      No models loaded from backend
                    </option>
                  )}
                </select>
                {selectedModel && (
                  <p className="text-[11px] text-slate-400 mt-1.5">
                    {models.find((m) => m.id === selectedModel)?.description}
                  </p>
                )}
              </div>

              {/* Temperature */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-medium text-slate-300">Temperature</span>
                  <span className="font-mono text-indigo-400">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-indigo-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>0.0 (Deterministic)</span>
                  <span>1.0 (Balanced)</span>
                  <span>2.0 (Creative)</span>
                </div>
              </div>

              {/* Streaming Toggle */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div>
                  <span className="text-xs font-medium text-slate-200 block">
                    Server-Sent Events (SSE) Streaming
                  </span>
                  <span className="text-[11px] text-slate-400">
                    Stream tokens in real-time as they are synthesized
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={enableStreaming}
                  onChange={(e) => setEnableStreaming(e.target.checked)}
                  className="w-4 h-4 accent-indigo-500 rounded cursor-pointer"
                />
              </div>

              {/* System Prompt */}
              <Textarea
                label="System Prompt (Optional)"
                placeholder="Set system-level constraints and identity..."
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={2}
              />

              {/* User Prompt */}
              <Textarea
                label="User Prompt / Task Goal"
                placeholder="Enter test prompt to dispatch through abstraction layer..."
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                rows={4}
                required
              />

              {/* Dispatch Action */}
              <div className="pt-2 flex items-center gap-3">
                {isStreaming || isLoading ? (
                  <Button
                    variant="destructive"
                    size="md"
                    icon={Square}
                    onClick={handleStop}
                    className="w-full"
                  >
                    Abort Execution
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="md"
                    icon={Play}
                    onClick={handleSubmit}
                    disabled={!userPrompt.trim() || !selectedModel}
                    className="w-full"
                  >
                    Execute via Abstraction Layer
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Execution Output & Telemetry */}
        <div className="lg:col-span-7 space-y-4">
          <Card className="flex flex-col h-full min-h-[500px]">
            <CardHeader className="flex flex-row items-center justify-between py-3.5">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <CardTitle className="text-sm">Response Stream</CardTitle>
              </div>

              <div className="flex items-center gap-2">
                {elapsedMs > 0 && (
                  <span className="inline-flex items-center gap-1 font-mono text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                    <Clock className="w-3 h-3 text-indigo-400" />
                    {(elapsedMs / 1000).toFixed(2)}s
                  </span>
                )}
                {output && (
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={copied ? Check : Copy}
                    onClick={handleCopy}
                    className="text-xs py-1 h-7"
                  >
                    {copied ? "Copied" : "Copy"}
                  </Button>
                )}
              </div>
            </CardHeader>

            <CardContent className="flex-1 p-4 bg-slate-950/90 rounded-b-xl font-mono text-xs overflow-y-auto flex flex-col justify-between">
              {output ? (
                <div className="text-slate-100 whitespace-pre-wrap leading-relaxed">
                  {output}
                  {isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse align-middle" />
                  )}
                </div>
              ) : isLoading ? (
                <div className="flex flex-col items-center justify-center flex-1 py-12 text-slate-400 space-y-3">
                  <Sparkles className="w-6 h-6 text-indigo-400 animate-spin" />
                  <span>Connecting to provider adapter...</span>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center flex-1 py-12 text-slate-400 space-y-2">
                  <Terminal className="w-8 h-8 text-slate-700" />
                  <span>Configure a prompt and dispatch to test LLM generation</span>
                </div>
              )}

              {/* Token Usage Footer Pill */}
              {tokenUsage && (
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5 font-medium text-slate-300">
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    <span>Token Telemetry:</span>
                  </div>
                  <div className="flex items-center gap-3 font-mono">
                    <span>
                      Prompt: <strong className="text-slate-200">{tokenUsage.input_tokens ?? "—"}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Completion: <strong className="text-slate-200">{tokenUsage.output_tokens ?? "—"}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Total: <strong className="text-indigo-300">{tokenUsage.total_tokens ?? "—"}</strong>
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

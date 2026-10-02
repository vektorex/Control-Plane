"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  Workflow,
  ArrowLeft,
  Plus,
  Play,
  Clock,
  Globe,
  GitBranch,
  Sliders,
  Sparkles,
  Pause,
  Trash2,
  Edit2,
  History,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  Loader2,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { workflowService } from "@/services/workflows";
import { triggerService } from "@/services/triggers";
import { TriggerBuilderModal } from "@/components/features/triggers/TriggerBuilderModal";
import { TriggerTestModal } from "@/components/features/triggers/TriggerTestModal";

const TYPE_CONFIGS = {
  schedule: {
    icon: Clock,
    label: "Schedule",
    color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  },
  webhook: {
    icon: Globe,
    label: "Webhook",
    color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  },
  connector_event: {
    icon: GitBranch,
    label: "GitHub Event",
    color: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  },
  manual: {
    icon: Play,
    label: "Manual",
    color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  },
};

export default function WorkflowTriggersPage({ params }) {
  const unwrappedParams = use(params);
  const { workflowId } = unwrappedParams;

  const [workflow, setWorkflow] = useState(null);
  const [triggers, setTriggers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [editingTrigger, setEditingTrigger] = useState(null);
  const [testingTrigger, setTestingTrigger] = useState(null);

  // Status message
  const [banner, setBanner] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [wf, trigList] = await Promise.all([
        workflowService.getWorkflow(workflowId),
        triggerService.listTriggers(workflowId),
      ]);
      setWorkflow(wf);
      setTriggers(trigList?.triggers || []);
    } catch (err) {
      console.error("[TriggersPage] Load error:", err);
      setError(err.message || "Failed to load workflow triggers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [workflowId]);

  const handlePauseResume = async (trig) => {
    try {
      if (trig.status === "active") {
        await triggerService.pauseTrigger(trig.id);
        setBanner({ type: "info", text: `Paused trigger '${trig.name}'.` });
      } else {
        await triggerService.resumeTrigger(trig.id);
        setBanner({ type: "success", text: `Resumed trigger '${trig.name}'.` });
      }
      loadData();
    } catch (err) {
      setError(err.message || "Failed to update trigger status.");
    }
  };

  const handleDelete = async (trig) => {
    if (!confirm(`Are you sure you want to delete trigger "${trig.name}"?`)) return;
    try {
      await triggerService.deleteTrigger(trig.id);
      setBanner({ type: "info", text: `Deleted trigger '${trig.name}'.` });
      loadData();
    } catch (err) {
      setError(err.message || "Failed to delete trigger.");
    }
  };

  const handleRunNow = async (trig) => {
    try {
      setBanner({ type: "info", text: `Executing trigger '${trig.name}'...` });
      const runRes = await triggerService.runManualTrigger(workflowId, trig.id, {});
      setBanner({
        type: "success",
        text: `Trigger executed! Run ID: ${runRes.id} (Status: ${runRes.status})`,
      });
      loadData();
    } catch (err) {
      setError(err.message || "Manual execution failed.");
    }
  };

  const handleCopyUrl = (publicId) => {
    const fullUrl = `${window.location.origin}/api/webhooks/${publicId}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedId(publicId);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
      {/* Top Header */}
      <div className="mb-6 flex flex-col gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href={`/app/workflows/${workflowId}`}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Workflow Editor</span>
            </Link>
          </div>
          <div className="mt-1 flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-white">
              {workflow?.name || "Workflow"} &mdash; Automated Triggers
            </h1>
            <Badge variant="outline" className="text-xs">
              {triggers.length} Trigger{triggers.length === 1 ? "" : "s"}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Define recurring schedules, incoming webhooks, and connector events to automatically start this pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href={`/app/workflows/${workflowId}/runs`}>
            <Button variant="outline" size="sm" className="text-xs gap-1.5">
              <History className="h-3.5 w-3.5" />
              <span>Workflow Runs</span>
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="text-xs gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setEditingTrigger(null);
              setIsBuilderOpen(true);
            }}
            className="gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Trigger</span>
          </Button>
        </div>
      </div>

      {/* Banner */}
      {banner && (
        <div
          className={`mb-4 flex items-center justify-between rounded-lg p-3 text-xs border ${
            banner.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-blue-500/10 border-blue-500/30 text-blue-300"
          }`}
        >
          <span>{banner.text}</span>
          <button onClick={() => setBanner(null)} className="text-slate-400 hover:text-slate-200">
            &times;
          </button>
        </div>
      )}

      {error && (
        <div className="mb-4 flex items-center justify-between rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-slate-200">
            &times;
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && triggers.length === 0 ? (
        <div className="flex items-center justify-center p-16">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
        </div>
      ) : triggers.length === 0 ? (
        /* Empty State */
        <Card className="flex flex-col items-center justify-center p-12 text-center border-slate-800 bg-slate-900/40">
          <Clock className="h-12 w-12 text-slate-600 mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">No Triggers Configured</h3>
          <p className="mt-1 max-w-sm text-xs text-slate-400">
            This workflow currently only executes when triggered manually. Add a schedule, webhook, or GitHub event trigger to automate execution.
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsBuilderOpen(true)}
            className="mt-4 gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Create First Trigger</span>
          </Button>
        </Card>
      ) : (
        /* Triggers Grid */
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {triggers.map((t) => {
            const typeConf = TYPE_CONFIGS[t.trigger_type] || TYPE_CONFIGS.manual;
            const Icon = typeConf.icon;
            const isActive = t.status === "active";

            return (
              <Card
                key={t.id}
                className="flex flex-col justify-between border-slate-800 bg-slate-900/60 p-5 hover:border-slate-700 transition-all"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`rounded-lg border p-1.5 ${typeConf.color}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm text-slate-100">{t.name}</h3>
                        <span className="text-[10px] text-slate-400">{typeConf.label}</span>
                      </div>
                    </div>

                    <Badge
                      className={`text-[10px] font-semibold ${
                        isActive
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {t.status.toUpperCase()}
                    </Badge>
                  </div>

                  {t.description && (
                    <p className="mt-2.5 text-xs text-slate-400 line-clamp-2">
                      {t.description}
                    </p>
                  )}

                  {/* Trigger Specific Details */}
                  <div className="mt-3.5 space-y-1.5 rounded-lg border border-slate-800/80 bg-slate-950/60 p-3 text-[11px]">
                    {t.trigger_type === "schedule" && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Cron Expression:</span>
                          <span className="font-mono text-indigo-300">
                            {t.configuration?.schedule?.expression || "0 * * * *"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Timezone:</span>
                          <span className="text-slate-300">
                            {t.configuration?.schedule?.timezone || "UTC"}
                          </span>
                        </div>
                        {t.next_run_at && (
                          <div className="flex justify-between">
                            <span className="text-slate-500">Next Due Run:</span>
                            <span className="text-amber-400 font-medium">
                              {new Date(t.next_run_at).toLocaleString()}
                            </span>
                          </div>
                        )}
                      </>
                    )}

                    {(t.trigger_type === "webhook" || t.trigger_type === "connector_event") && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">Webhook URL:</span>
                          {t.public_trigger_id ? (
                            <button
                              type="button"
                              onClick={() => handleCopyUrl(t.public_trigger_id)}
                              className="flex items-center gap-1 font-mono text-[10px] text-indigo-400 hover:text-indigo-300"
                              title="Copy Webhook Endpoint"
                            >
                              {copiedId === t.public_trigger_id ? (
                                <>
                                  <Check className="h-3 w-3 text-emerald-400" />
                                  <span className="text-emerald-400">Copied</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="h-3 w-3" />
                                  <span>/api/webhooks/{t.public_trigger_id.slice(0, 10)}...</span>
                                </>
                              )}
                            </button>
                          ) : (
                            <span className="text-slate-500">None</span>
                          )}
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Signature:</span>
                          <span className="text-emerald-400 font-medium">HMAC-SHA256 Protected</span>
                        </div>
                      </>
                    )}

                    {t.filter_configuration?.rules?.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Filters:</span>
                        <span className="text-indigo-300">
                          {t.filter_configuration.rules.length} rule{t.filter_configuration.rules.length === 1 ? "" : "s"} ({t.filter_configuration.logic || "AND"})
                        </span>
                      </div>
                    )}

                    {t.debounce_seconds > 0 && (
                      <div className="flex justify-between">
                        <span className="text-slate-500">Debounce:</span>
                        <span className="text-slate-300">{t.debounce_seconds}s</span>
                      </div>
                    )}
                  </div>

                  {/* Run Metrics */}
                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-2.5">
                    <div className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      <span>{t.success_count || 0} passed</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <XCircle className="h-3.5 w-3.5 text-rose-400" />
                      <span>{t.failure_count || 0} failed</span>
                    </div>
                    <div>
                      {t.last_triggered_at ? (
                        <span>Last: {new Date(t.last_triggered_at).toLocaleDateString()}</span>
                      ) : (
                        <span className="text-slate-600">Never executed</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="mt-4 flex items-center justify-between border-t border-slate-800 pt-3 text-xs">
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handlePauseResume(t)}
                      className="h-7 px-2 text-[11px] text-slate-300 hover:text-white"
                      title={isActive ? "Pause trigger" : "Resume trigger"}
                    >
                      {isActive ? <Pause className="h-3 w-3 mr-1" /> : <Play className="h-3 w-3 mr-1" />}
                      {isActive ? "Pause" : "Resume"}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setTestingTrigger(t)}
                      className="h-7 px-2 text-[11px] text-indigo-400 hover:text-indigo-300"
                    >
                      <Sparkles className="h-3 w-3 mr-1" />
                      Test
                    </Button>

                    <Link href={`/app/triggers/${t.id}/runs`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-[11px] text-slate-400 hover:text-slate-200"
                      >
                        <History className="h-3 w-3 mr-1" />
                        Runs
                      </Button>
                    </Link>
                  </div>

                  <div className="flex items-center gap-1">
                    {t.trigger_type === "manual" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRunNow(t)}
                        className="h-7 px-2 text-[11px] text-emerald-400 hover:text-emerald-300"
                        title="Run Now"
                      >
                        <Play className="h-3 w-3" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditingTrigger(t);
                        setIsBuilderOpen(true);
                      }}
                      className="h-7 px-2 text-[11px] text-slate-400 hover:text-slate-200"
                    >
                      <Edit2 className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(t)}
                      className="h-7 px-2 text-[11px] text-rose-400 hover:text-rose-300"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Trigger Builder Modal */}
      <TriggerBuilderModal
        workflowId={workflowId}
        existingTrigger={editingTrigger}
        isOpen={isBuilderOpen}
        onClose={() => {
          setIsBuilderOpen(false);
          setEditingTrigger(null);
        }}
        onSaved={() => {
          loadData();
        }}
      />

      {/* Trigger Dry-Run Test Modal */}
      <TriggerTestModal
        trigger={testingTrigger}
        isOpen={Boolean(testingTrigger)}
        onClose={() => setTestingTrigger(null)}
      />
    </div>
  );
}

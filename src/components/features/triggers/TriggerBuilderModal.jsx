"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Plus,
  Save,
  Clock,
  Globe,
  GitBranch,
  Play,
  Key,
  ShieldAlert,
  Loader2,
  Copy,
  Check,
  Calendar,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { triggerService } from "@/services/triggers";
import { EventFilterBuilder } from "./EventFilterBuilder";

const TRIGGER_TYPES = [
  {
    type: "schedule",
    name: "Schedule (Cron)",
    icon: Clock,
    desc: "Run automatically on recurring schedule or cron expression.",
    color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  },
  {
    type: "webhook",
    name: "Webhook Ingestion",
    icon: Globe,
    desc: "Run on incoming HTTP requests with HMAC signature validation.",
    color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  },
  {
    type: "connector_event",
    name: "GitHub Event",
    icon: GitBranch,
    desc: "Run on normalized GitHub events (issues, pull requests).",
    color: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  },
  {
    type: "manual",
    name: "Manual / API",
    icon: Play,
    desc: "Explicit trigger via user button or authenticated API call.",
    color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  },
];

const TIMEZONES = [
  "UTC",
  "Asia/Kolkata",
  "America/New_York",
  "America/Los_Angeles",
  "America/Chicago",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
];

const GITHUB_EVENTS = [
  { id: "github.issue.created", label: "GitHub Issue Created" },
  { id: "github.issue.updated", label: "GitHub Issue Updated" },
  { id: "github.pull_request.opened", label: "GitHub Pull Request Opened" },
  { id: "github.pull_request.updated", label: "GitHub Pull Request Updated" },
];

export function TriggerBuilderModal({
  workflowId,
  existingTrigger = null,
  isOpen,
  onClose,
  onSaved,
}) {
  if (!isOpen) return null;

  const isEditing = Boolean(existingTrigger);

  const [name, setName] = useState(existingTrigger?.name || "");
  const [description, setDescription] = useState(existingTrigger?.description || "");
  const [triggerType, setTriggerType] = useState(existingTrigger?.trigger_type || "schedule");

  // Schedule states
  const [cronExpression, setCronExpression] = useState(
    existingTrigger?.configuration?.schedule?.expression || "0 * * * *"
  );
  const [scheduleTimezone, setScheduleTimezone] = useState(
    existingTrigger?.configuration?.schedule?.timezone || "UTC"
  );
  const [schedulePreset, setSchedulePreset] = useState("hourly");

  // GitHub states
  const [githubEvent, setGithubEvent] = useState(
    existingTrigger?.configuration?.github_event || "github.issue.created"
  );
  const [repository, setRepository] = useState(
    existingTrigger?.configuration?.repository || ""
  );

  // Filter & Debounce states
  const [filterConfig, setFilterConfig] = useState(
    existingTrigger?.filter_configuration || { logic: "AND", rules: [] }
  );
  const [debounceSeconds, setDebounceSeconds] = useState(
    existingTrigger?.debounce_seconds || 0
  );
  const [maxRetries, setMaxRetries] = useState(
    existingTrigger?.retry_configuration?.max_retries || 2
  );

  // Input mapping
  const [inputMappingText, setInputMappingText] = useState(
    JSON.stringify(existingTrigger?.configuration?.input_mapping || {}, null, 2)
  );

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [newSecretBanner, setNewSecretBanner] = useState(null);
  const [copiedSecret, setCopiedSecret] = useState(false);

  const handlePresetChange = (preset) => {
    setSchedulePreset(preset);
    if (preset === "hourly") setCronExpression("0 * * * *");
    else if (preset === "daily") setCronExpression("0 0 * * *");
    else if (preset === "weekly") setCronExpression("0 0 * * 0");
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError("Please provide a name for this trigger.");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      let parsedInputMapping = {};
      try {
        parsedInputMapping = JSON.parse(inputMappingText || "{}");
      } catch (err) {
        throw new Error("Invalid JSON in Input Mapping configuration.");
      }

      const configuration = {
        input_mapping: parsedInputMapping,
      };

      if (triggerType === "schedule") {
        configuration.schedule = {
          kind: "cron",
          expression: cronExpression,
          timezone: scheduleTimezone,
        };
      } else if (triggerType === "connector_event") {
        configuration.connector_type = "github";
        configuration.github_event = githubEvent;
        if (repository) configuration.repository = repository;
      }

      const payload = {
        name,
        description,
        trigger_type: triggerType,
        configuration,
        filter_configuration: filterConfig,
        retry_configuration: {
          max_retries: Number(maxRetries),
          backoff_factor: 2.0,
        },
        debounce_seconds: Number(debounceSeconds),
      };

      if (isEditing) {
        const updated = await triggerService.updateTrigger(existingTrigger.id, payload);
        onSaved(updated);
        onClose();
      } else {
        const created = await triggerService.createTrigger(workflowId, payload);
        if (created.webhook_secret) {
          // Keep modal open to show secret once!
          setNewSecretBanner({
            secret: created.webhook_secret,
            publicUrl: `/api/webhooks/${created.public_trigger_id}`,
          });
          onSaved(created);
        } else {
          onSaved(created);
          onClose();
        }
      }
    } catch (err) {
      console.error("[TriggerBuilder] Error saving trigger:", err);
      setError(err.message || "Failed to save workflow trigger.");
    } finally {
      setSaving(false);
    }
  };

  const handleCopySecret = () => {
    if (newSecretBanner?.secret) {
      navigator.clipboard.writeText(newSecretBanner.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="flex max-h-[92vh] w-full max-w-3xl flex-col rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <Clock className="h-5 w-5 text-indigo-400" />
            <div>
              <h2 className="text-sm font-semibold text-slate-100">
                {isEditing ? `Edit Trigger: ${existingTrigger.name}` : "Create Workflow Trigger"}
              </h2>
              <p className="text-[11px] text-slate-400">
                Configure automated execution rules, schedules, and event filters.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-4 text-xs">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Webhook Secret Generated Banner */}
          {newSecretBanner && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <Key className="h-4 w-4" />
                <span>Webhook Trigger Created &mdash; Save Secret Now</span>
              </div>
              <p className="text-[11px] text-slate-300">
                This secret token will <strong className="text-white">never be displayed again</strong>. Use it to compute HMAC-SHA256 signatures on your external requests.
              </p>
              <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-slate-950 p-2 font-mono text-[11px] text-emerald-300">
                <span className="flex-1 truncate">{newSecretBanner.secret}</span>
                <button
                  type="button"
                  onClick={handleCopySecret}
                  className="flex items-center gap-1 rounded bg-emerald-600/30 px-2 py-1 text-[10px] text-emerald-200 hover:bg-emerald-600/50"
                >
                  {copiedSecret ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  {copiedSecret ? "Copied" : "Copy"}
                </button>
              </div>
              <div className="pt-1">
                <span className="text-[11px] text-slate-400">Endpoint URL: </span>
                <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[11px] text-slate-200">
                  {newSecretBanner.publicUrl}
                </code>
              </div>
              <div className="flex justify-end pt-2">
                <Button size="sm" variant="outline" onClick={onClose} className="text-xs">
                  Done & Close
                </Button>
              </div>
            </div>
          )}

          {/* Name & Description */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block font-semibold text-slate-300">Trigger Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Daily Sync or GitHub PR Review"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block font-semibold text-slate-300">Description</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional purpose of this trigger"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Trigger Type Selection */}
          {!isEditing && (
            <div>
              <label className="mb-2 block font-semibold text-slate-300">Select Trigger Type</label>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {TRIGGER_TYPES.map((t) => {
                  const Icon = t.icon;
                  const isSelected = triggerType === t.type;
                  return (
                    <div
                      key={t.type}
                      onClick={() => setTriggerType(t.type)}
                      className={`cursor-pointer rounded-xl border p-3 transition-all ${
                        isSelected
                          ? "border-indigo-500 bg-indigo-500/10 shadow-sm"
                          : "border-slate-800 bg-slate-950 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`rounded-lg border p-1.5 ${t.color}`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <span className="font-semibold text-slate-200">{t.name}</span>
                      </div>
                      <p className="mt-1.5 text-[11px] text-slate-400">{t.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Type Specific Fields */}
          {triggerType === "schedule" && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
              <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-400">
                Schedule Configuration
              </span>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div>
                  <label className="mb-1 block text-slate-300">Frequency</label>
                  <select
                    value={schedulePreset}
                    onChange={(e) => handlePresetChange(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="hourly">Every Hour (0 * * * *)</option>
                    <option value="daily">Every Day at Midnight (0 0 * * *)</option>
                    <option value="weekly">Every Sunday (0 0 * * 0)</option>
                    <option value="custom">Custom Cron Expression</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-slate-300">Cron Expression *</label>
                  <input
                    type="text"
                    value={cronExpression}
                    onChange={(e) => {
                      setCronExpression(e.target.value);
                      setSchedulePreset("custom");
                    }}
                    placeholder="0 * * * *"
                    className="w-full font-mono rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-slate-300">Timezone *</label>
                  <select
                    value={scheduleTimezone}
                    onChange={(e) => setScheduleTimezone(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {triggerType === "connector_event" && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
              <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-400">
                GitHub Event Configuration
              </span>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-slate-300">GitHub Event Type</label>
                  <select
                    value={githubEvent}
                    onChange={(e) => setGithubEvent(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    {GITHUB_EVENTS.map((ge) => (
                      <option key={ge.id} value={ge.id}>
                        {ge.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-slate-300">Repository (optional filter)</label>
                  <input
                    type="text"
                    value={repository}
                    onChange={(e) => setRepository(e.target.value)}
                    placeholder="e.g. org/repo-name"
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Event Filter Builder */}
          <EventFilterBuilder filterConfig={filterConfig} onChange={setFilterConfig} />

          {/* Input Payload Mapping & Retries */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="font-semibold text-slate-300">Input Mapping (JSON)</label>
                <span className="text-[10px] text-slate-500 font-mono">
                  &#123;&#123;payload.x.y&#125;&#125;
                </span>
              </div>
              <textarea
                rows={4}
                value={inputMappingText}
                onChange={(e) => setInputMappingText(e.target.value)}
                placeholder='{"ticket_title": "{{payload.issue.title}}"}'
                className="w-full font-mono rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-[11px] text-indigo-300 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="space-y-3">
              <div>
                <label className="mb-1 block font-semibold text-slate-300">
                  Debounce Window (Seconds)
                </label>
                <input
                  type="number"
                  min="0"
                  max="3600"
                  value={debounceSeconds}
                  onChange={(e) => setDebounceSeconds(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                />
                <span className="mt-1 block text-[10px] text-slate-500">
                  Suppresses rapid burst events within this window (max 3600s).
                </span>
              </div>

              <div>
                <label className="mb-1 block font-semibold text-slate-300">Max Retries</label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={maxRetries}
                  onChange={(e) => setMaxRetries(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
                />
                <span className="mt-1 block text-[10px] text-slate-500">
                  Only retries transient provider / timeout failures with exponential backoff.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-slate-800 px-6 py-3">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={saving}
            className="gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            {isEditing ? "Save Changes" : "Create Trigger"}
          </Button>
        </div>
      </div>
    </div>
  );
}

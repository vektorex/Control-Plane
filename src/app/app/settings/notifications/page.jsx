"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Bell,
  Settings,
  Radio,
  Mail,
  Smartphone,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Send,
  Save,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { notificationService } from "@/services/notifications";

const EVENT_GROUPS = [
  {
    name: "Workflows",
    events: [
      { id: "workflow.completed", label: "Workflow Completed", desc: "Sent when an execution succeeds" },
      { id: "workflow.failed", label: "Workflow Failed", desc: "Sent when an execution fails or errors" },
      { id: "workflow.waiting_for_approval", label: "Approval Required", desc: "HITL human approval checkpoint", mandatoryInApp: true },
    ],
  },
  {
    name: "Triggers & Automations",
    events: [
      { id: "trigger.completed", label: "Trigger Completed", desc: "Scheduled or webhook trigger invoked successfully" },
      { id: "trigger.failed", label: "Trigger Failed", desc: "Automated trigger execution failed" },
    ],
  },
  {
    name: "Background Jobs",
    events: [
      { id: "job.completed", label: "Job Completed", desc: "Asynchronous task completed" },
      { id: "job.retrying", label: "Job Retrying", desc: "Transient error encountered, retrying" },
      { id: "job.failed", label: "Job Failed", desc: "Permanent job failure" },
    ],
  },
  {
    name: "Evaluation & Quality",
    events: [
      { id: "evaluation.completed", label: "Evaluation Run Completed", desc: "Benchmark experiment finished" },
      { id: "evaluation.regression_detected", label: "Regression Detected", desc: "Accuracy or metric regression alert" },
    ],
  },
  {
    name: "Connectors & System",
    events: [
      { id: "connector.completed", label: "Connector Completed", desc: "External sync or operation succeeded" },
      { id: "connector.failed", label: "Connector Failed", desc: "External sync or operation failed" },
      { id: "system.warning", label: "System Warning", desc: "Resource or security alerts", mandatoryInApp: true },
    ],
  },
];

export default function NotificationSettingsPage() {
  const [preferences, setPreferences] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [testStatus, setTestStatus] = useState(null);

  useEffect(() => {
    fetchPrefs();
  }, []);

  const fetchPrefs = async () => {
    setLoading(true);
    try {
      const res = await notificationService.getPreferences();
      const prefMap = {};
      if (res?.preferences) {
        res.preferences.forEach((p) => {
          const key = `${p.event_type}:${p.channel}`;
          prefMap[key] = p.enabled;
        });
      }
      setPreferences(prefMap);
    } catch (err) {
      console.error("Failed to load notification preferences:", err);
    } finally {
      setLoading(false);
    }
  };

  const isEnabled = (eventType, channel, mandatoryInApp = false) => {
    if (channel === "in_app" && mandatoryInApp) return true;
    const key = `${eventType}:${channel}`;
    if (preferences[key] !== undefined) return preferences[key];
    // Default: in_app enabled, external disabled
    return channel === "in_app";
  };

  const togglePreference = (eventType, channel, mandatoryInApp = false) => {
    if (channel === "in_app" && mandatoryInApp) return; // Cannot disable mandatory
    const key = `${eventType}:${channel}`;
    const current = isEnabled(eventType, channel, mandatoryInApp);
    setPreferences((prev) => ({
      ...prev,
      [key]: !current,
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const payload = [];
      EVENT_GROUPS.forEach((g) => {
        g.events.forEach((ev) => {
          ["in_app", "webhook", "email"].forEach((ch) => {
            const enabled = isEnabled(ev.id, ch, ev.mandatoryInApp);
            payload.push({
              event_type: ev.id,
              channel: ch,
              enabled,
            });
          });
        });
      });
      await notificationService.updatePreferences(payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Settings className="w-6 h-6 text-indigo-400" />
            Notification Preferences
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Configure delivery channels, destinations, and event routing preferences for your workspace.
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2">
          <Link
            href="/app/settings/webhooks"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:border-slate-700 hover:text-white transition-colors"
          >
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            Manage Webhooks
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors shadow-sm"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Changes
          </button>
        </div>
      </div>

      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 text-xs animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Notification preferences updated successfully.</span>
        </div>
      )}

      {/* Channel Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* In-App */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
              <Smartphone className="w-4 h-4" />
              In-App Center
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/60">
              Active
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Internal real-time notification drawer and bell badges for authenticated workspace users.
          </p>
        </div>

        {/* Webhooks */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
              <Radio className="w-4 h-4" />
              Outbound Webhooks
            </div>
            <Link
              href="/app/settings/webhooks"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              Configure →
            </Link>
          </div>
          <p className="text-xs text-slate-400">
            HMAC-SHA256 signed POST events to configured HTTP destinations with SSRF protection.
          </p>
        </div>

        {/* Email */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <Mail className="w-4 h-4" />
              Email Delivery
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono text-slate-400 bg-slate-800">
              Provider-Agnostic
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Delivers sanitized email alerts via configured provider (SendGrid, SES, Resend, or SMTP).
          </p>
        </div>
      </div>

      {/* Preferences Matrix */}
      <div className="border border-slate-800/80 rounded-xl overflow-hidden bg-slate-950/40">
        <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Event Notification Matrix</h3>
            <p className="text-xs text-slate-400">
              Toggle which channels receive notifications for each specific system event.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400 mb-2" />
            <p className="text-xs">Loading preferences...</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {EVENT_GROUPS.map((group) => (
              <div key={group.name} className="p-4 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  {group.name}
                </h4>

                <div className="space-y-2">
                  {group.events.map((ev) => {
                    const inAppOn = isEnabled(ev.id, "in_app", ev.mandatoryInApp);
                    const webhookOn = isEnabled(ev.id, "webhook");
                    const emailOn = isEnabled(ev.id, "email");

                    return (
                      <div
                        key={ev.id}
                        className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3 rounded-lg bg-slate-900/40 hover:bg-slate-900/70 border border-slate-850 transition-colors"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-slate-200">
                              {ev.label}
                            </span>
                            <span className="text-[10px] font-mono text-slate-500">
                              {ev.id}
                            </span>
                            {ev.mandatoryInApp && (
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-amber-950/80 text-amber-300 border border-amber-800/50">
                                Required In-App
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-400">{ev.desc}</p>
                        </div>

                        {/* Channel Toggles */}
                        <div className="flex items-center gap-4 text-xs shrink-0 self-end sm:self-auto">
                          {/* In-App Toggle */}
                          <label className="flex items-center gap-1.5 cursor-pointer select-none">
                            <input
                              type="checkbox"
                              checked={inAppOn}
                              disabled={ev.mandatoryInApp}
                              onChange={() => togglePreference(ev.id, "in_app", ev.mandatoryInApp)}
                              className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0 focus:outline-none"
                            />
                            <span className="text-slate-300 text-xs">In-App</span>
                          </label>

                          {/* Webhook Toggle */}
                          <label className="flex items-center gap-1.5 cursor-pointer select-none">
                            <input
                              type="checkbox"
                              checked={webhookOn}
                              onChange={() => togglePreference(ev.id, "webhook")}
                              className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0 focus:outline-none"
                            />
                            <span className="text-slate-300 text-xs">Webhook</span>
                          </label>

                          {/* Email Toggle */}
                          <label className="flex items-center gap-1.5 cursor-pointer select-none">
                            <input
                              type="checkbox"
                              checked={emailOn}
                              onChange={() => togglePreference(ev.id, "email")}
                              className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0 focus:outline-none"
                            />
                            <span className="text-slate-300 text-xs">Email</span>
                          </label>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

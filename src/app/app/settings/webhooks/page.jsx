"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Radio,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  RotateCw,
  Trash2,
  ExternalLink,
  ShieldAlert,
  Send,
  ArrowLeft,
  X,
  Eye,
  EyeOff,
} from "lucide-react";
import { notificationService } from "@/services/notifications";

const ALL_EVENT_OPTIONS = [
  "workflow.completed",
  "workflow.failed",
  "workflow.waiting_for_approval",
  "trigger.completed",
  "trigger.failed",
  "job.completed",
  "job.failed",
  "job.retrying",
  "document.processing_completed",
  "document.processing_failed",
  "evaluation.completed",
  "evaluation.regression_detected",
  "replay.completed",
  "replay.failed",
  "connector.completed",
  "connector.failed",
  "system.warning",
];

export default function WebhookManagementPage() {
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [testResult, setTestStatus] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [revealedSecret, setRevealedSecret] = useState(null); // { secret, name }
  const [copied, setCopied] = useState(false);

  // Form states for Create
  const [formData, setFormData] = useState({
    name: "",
    url: "",
    subscribed_events: ["*"],
    active: true,
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const fetchEndpoints = useCallback(async () => {
    setLoading(true);
    try {
      const res = await notificationService.listWebhookEndpoints();
      setEndpoints(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("Failed to load webhook endpoints:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEndpoints();
  }, [fetchEndpoints]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError("");
    try {
      const res = await notificationService.createWebhookEndpoint({
        name: formData.name,
        url: formData.url,
        subscribed_events: formData.subscribed_events,
        active: formData.active,
      });

      // Show secret once!
      if (res?.secret) {
        setRevealedSecret({
          secret: res.secret,
          name: res.name,
          title: "Webhook Endpoint Created",
        });
      }

      setCreateModalOpen(false);
      setFormData({ name: "", url: "", subscribed_events: ["*"], active: true });
      fetchEndpoints();
    } catch (err) {
      setFormError(err.message || "Failed to create webhook endpoint.");
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleToggleActive = async (ep) => {
    try {
      await notificationService.updateWebhookEndpoint(ep.id, {
        active: !ep.active,
      });
      setEndpoints((prev) =>
        prev.map((e) => (e.id === ep.id ? { ...e, active: !e.active } : e))
      );
    } catch (err) {
      console.error("Failed to toggle webhook active state:", err);
    }
  };

  const handleTestEndpoint = async (epId) => {
    setTestingId(epId);
    setTestStatus(null);
    try {
      const res = await notificationService.testWebhookEndpoint(epId);
      setTestStatus(res);
      fetchEndpoints();
    } catch (err) {
      setTestStatus({
        success: false,
        error_message: err.message || "Test dispatch failed",
        endpoint_id: epId,
      });
    } finally {
      setTestingId(null);
    }
  };

  const handleRotateSecret = async (ep) => {
    if (!confirm(`Are you sure you want to rotate the HMAC secret for '${ep.name}'? Existing signatures will become invalid immediately.`)) {
      return;
    }
    try {
      const res = await notificationService.rotateWebhookSecret(ep.id);
      if (res?.secret) {
        setRevealedSecret({
          secret: res.secret,
          name: ep.name,
          title: "Webhook Signing Secret Rotated",
        });
      }
    } catch (err) {
      alert("Failed to rotate secret: " + err.message);
    }
  };

  const handleDelete = async (epId) => {
    if (!confirm("Are you sure you want to delete this webhook destination? This cannot be undone.")) {
      return;
    }
    try {
      await notificationService.deleteWebhookEndpoint(epId);
      setEndpoints((prev) => prev.filter((e) => e.id !== epId));
    } catch (err) {
      alert("Failed to delete webhook endpoint: " + err.message);
    }
  };

  const copySecret = () => {
    if (!revealedSecret?.secret) return;
    navigator.clipboard.writeText(revealedSecret.secret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/app/settings/notifications"
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Notification Settings
            </Link>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Radio className="w-6 h-6 text-cyan-400" />
            Outbound Webhook Destinations
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Configure secure HMAC-SHA256 authenticated webhook endpoints with SSRF protection and deterministic payload delivery.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Add Webhook Destination
        </button>
      </div>

      {/* Secret Reveal Banner (Shown only once) */}
      {revealedSecret && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/60 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-sm">
              <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
              <span>{revealedSecret.title}: {revealedSecret.name}</span>
            </div>
            <button
              onClick={() => setRevealedSecret(null)}
              className="p-1 rounded-lg text-amber-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="text-xs text-amber-200/80">
            Copy your HMAC-SHA256 signing secret now. For security purposes, this secret is hashed and will <strong>never be shown again</strong>.
          </p>

          <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-amber-900/60 font-mono text-xs text-amber-300">
            <span className="truncate flex-1 select-all">{revealedSecret.secret}</span>
            <button
              onClick={copySecret}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 transition-colors shrink-0"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Test Result Toast/Banner */}
      {testResult && (
        <div
          className={`flex items-start justify-between p-3.5 rounded-xl border text-xs animate-in fade-in duration-200 ${
            testResult.success
              ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
              : "bg-rose-950/40 border-rose-800/60 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>
              <strong>Test Result:</strong>{" "}
              {testResult.success
                ? `Synthetic test payload successfully received (HTTP ${testResult.status_code || 200}, ${testResult.latency_ms || 0}ms)`
                : `Test delivery failed: ${testResult.error_message || "Unknown error"}`}
            </span>
          </div>
          <button onClick={() => setTestStatus(null)} className="p-1 text-slate-400 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Endpoints List */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
          <p className="text-sm">Loading webhook endpoints...</p>
        </div>
      ) : endpoints.length === 0 ? (
        <div className="py-20 text-center rounded-2xl bg-slate-900/30 border border-slate-800/60 p-8 space-y-3">
          <Radio className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No Webhook Endpoints Configured</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Add an HTTPS destination to receive signed JSON event notifications for workflows, jobs, and approvals.
          </p>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add First Webhook
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {endpoints.map((ep) => (
            <div
              key={ep.id}
              className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
            >
              {/* Endpoint Information */}
              <div className="space-y-1.5 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h4 className="text-sm font-bold text-white">{ep.name}</h4>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      ep.active
                        ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}
                  >
                    {ep.active ? "Active" : "Disabled"}
                  </span>
                </div>

                <div className="font-mono text-xs text-slate-300 break-all select-all">
                  {ep.url}
                </div>

                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                  <span>
                    Subscribed:{" "}
                    <span className="text-slate-300 font-mono">
                      {ep.subscribed_events?.includes("*")
                        ? "All Events (*)"
                        : ep.subscribed_events?.join(", ")}
                    </span>
                  </span>

                  {ep.last_success_at && (
                    <span className="text-emerald-400">
                      Last success: {new Date(ep.last_success_at).toLocaleString()}
                    </span>
                  )}

                  {ep.last_failure_at && (
                    <span className="text-rose-400">
                      Last failure: {new Date(ep.last_failure_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>

              {/* Endpoint Control Actions */}
              <div className="flex flex-wrap items-center gap-2 shrink-0 self-end md:self-center">
                {/* Test button */}
                <button
                  onClick={() => handleTestEndpoint(ep.id)}
                  disabled={testingId === ep.id}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 transition-colors"
                  title="Dispatch synthetic test event"
                >
                  <Send className={`w-3 h-3 ${testingId === ep.id ? "animate-pulse" : ""}`} />
                  {testingId === ep.id ? "Testing..." : "Test"}
                </button>

                {/* Enable/Disable toggle */}
                <button
                  onClick={() => handleToggleActive(ep)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                    ep.active
                      ? "text-amber-400 hover:bg-amber-950/40 border-amber-800/50"
                      : "text-emerald-400 hover:bg-emerald-950/40 border-emerald-800/50"
                  }`}
                >
                  {ep.active ? "Disable" : "Enable"}
                </button>

                {/* Rotate Secret */}
                <button
                  onClick={() => handleRotateSecret(ep)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800 transition-colors"
                  title="Rotate HMAC signing secret"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                </button>

                {/* Delete button */}
                <button
                  onClick={() => handleDelete(ep.id)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 border border-slate-800 transition-colors"
                  title="Delete webhook destination"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Webhook Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Radio className="w-5 h-5 text-indigo-400" />
                Register Webhook Destination
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="p-1 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Destination Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Production Slack Ingestion, PagerDuty Alert"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Target HTTPS URL
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://api.yourdomain.com/webhooks/ai-work"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Must be a valid HTTPS URL. Localhost, loopback, private RFC1918 ranges, and cloud metadata IPs are rejected by SSRF guard.
                </span>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">
                  Subscribed Events
                </label>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2 max-h-40 overflow-y-auto">
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-200">
                    <input
                      type="checkbox"
                      checked={formData.subscribed_events.includes("*")}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({ ...formData, subscribed_events: ["*"] });
                        } else {
                          setFormData({ ...formData, subscribed_events: ["workflow.completed"] });
                        }
                      }}
                      className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                    />
                    <span>All Events (*)</span>
                  </label>

                  {!formData.subscribed_events.includes("*") && (
                    <div className="space-y-1 pt-1 pl-4 border-l border-slate-800">
                      {ALL_EVENT_OPTIONS.map((ev) => (
                        <label key={ev} className="flex items-center gap-2 cursor-pointer text-slate-400 hover:text-slate-200">
                          <input
                            type="checkbox"
                            checked={formData.subscribed_events.includes(ev)}
                            onChange={(e) => {
                              const current = formData.subscribed_events;
                              if (e.target.checked) {
                                setFormData({
                                  ...formData,
                                  subscribed_events: [...current, ev],
                                });
                              } else {
                                setFormData({
                                  ...formData,
                                  subscribed_events: current.filter((x) => x !== ev),
                                });
                              }
                            }}
                            className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                          />
                          <span className="font-mono text-[11px]">{ev}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="activeCheck"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                />
                <label htmlFor="activeCheck" className="text-slate-300 font-medium cursor-pointer">
                  Activate endpoint immediately upon creation
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className="px-4 py-1.5 rounded-lg font-medium bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors shadow-sm"
                >
                  {formSubmitting ? "Registering..." : "Create Webhook"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

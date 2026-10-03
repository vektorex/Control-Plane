"use client";

import React, { useState } from "react";
import { Webhook, Plus, Trash2, CheckCircle2, AlertCircle, Copy, Check, AlertTriangle, X } from "lucide-react";
import { developerService } from "@/services/developer";

export function WebhookTable({ webhooks = [], onRefresh, onOpenCreateModal }) {
  const [deletingId, setDeletingId] = useState(null);

  async function handleDelete(id) {
    if (!confirm("Are you sure you want to remove this webhook subscription?")) return;
    setDeletingId(id);
    try {
      await developerService.deleteWebhook(id);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err?.message || "Failed to delete webhook");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Webhook className="w-5 h-5 text-purple-500" />
          <h3 className="font-semibold text-neutral-900 dark:text-neutral-100">
            Webhook Subscriptions
          </h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
            {webhooks.length}
          </span>
        </div>

        {onOpenCreateModal && (
          <button
            onClick={onOpenCreateModal}
            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition-colors"
          >
            + New Webhook
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-neutral-50 dark:bg-neutral-800/50 text-neutral-500 dark:text-neutral-400 text-xs border-b border-neutral-200 dark:border-neutral-800">
            <tr>
              <th className="px-4 py-3 font-medium">Target URL</th>
              <th className="px-4 py-3 font-medium">Subscribed Events</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Failures</th>
              <th className="px-4 py-3 font-medium">Last Delivery</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
            {webhooks.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-neutral-500 dark:text-neutral-400 text-xs">
                  No webhooks configured. Register an HTTPS endpoint to receive event callbacks.
                </td>
              </tr>
            ) : (
              webhooks.map((sub) => (
                <tr key={sub.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-neutral-800 dark:text-neutral-200 truncate max-w-xs">
                    {sub.url}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {(sub.events || []).map((ev, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 font-mono"
                        >
                          {ev}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                        sub.status === "active"
                          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                          : "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
                      }`}
                    >
                      {sub.status === "active" ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                      {sub.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-600 dark:text-neutral-400 font-mono">
                    {sub.failure_count || 0}
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-500 dark:text-neutral-400">
                    {sub.last_delivery_at ? new Date(sub.last_delivery_at).toLocaleString() : "Never"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(sub.id)}
                      disabled={deletingId === sub.id}
                      className="p-1 rounded text-neutral-400 hover:text-rose-600 transition-colors"
                      title="Delete webhook"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function WebhookModal({ isOpen, onClose, applicationId, onCreated }) {
  const [url, setUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState([
    "run.completed",
    "run.failed",
    "workflow.completed",
  ]);
  const [createdSecret, setCreatedSecret] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const ALL_EVENTS = [
    "run.completed",
    "run.failed",
    "workflow.completed",
    "workflow.failed",
    "artifact.processed",
    "evaluation.completed",
    "security.incident.created",
    "usage.threshold",
    "recovery.failure",
  ];

  function toggleEvent(ev) {
    if (selectedEvents.includes(ev)) {
      setSelectedEvents(selectedEvents.filter((e) => e !== ev));
    } else {
      setSelectedEvents([...selectedEvents, ev]);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!url.trim() || selectedEvents.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      const res = await developerService.createWebhook(applicationId, {
        url: url.trim(),
        events: selectedEvents,
      });
      setCreatedSecret(res.webhook_secret);
      if (onCreated) onCreated();
    } catch (err) {
      setError(err?.message || "Failed to create webhook subscription");
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    if (createdSecret) {
      navigator.clipboard.writeText(createdSecret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  }

  function handleClose() {
    setUrl("");
    setCreatedSecret(null);
    setError(null);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
          <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
            {createdSecret ? "Webhook Created" : "Create Webhook Subscription"}
          </h3>
          <button onClick={handleClose} className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        {createdSecret ? (
          <div className="p-5 space-y-4">
            <div className="p-3.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div className="text-xs text-amber-700 dark:text-amber-300">
                <span className="font-semibold">Copy your signing secret now.</span> Use this secret with the SDK to verify incoming HMAC-SHA256 signatures on the <code>X-AWL-Signature</code> header.
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1">
                Webhook Signing Secret
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={createdSecret}
                  className="w-full font-mono text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 select-all"
                />
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white shrink-0 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={handleClose}
                className="text-xs px-4 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 dark:bg-neutral-100 dark:hover:bg-white text-white dark:text-neutral-900 font-medium"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleCreate} className="p-4 space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 text-xs border border-rose-200 dark:border-rose-900">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                Target Endpoint URL *
              </label>
              <input
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://api.yourdomain.com/webhooks/awl"
                className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                Must use HTTPS. Private IP addresses and loopback addresses are blocked.
              </p>
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Subscribed Events *
              </label>
              <div className="grid grid-cols-2 gap-2 p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
                {ALL_EVENTS.map((ev) => (
                  <label key={ev} className="flex items-center gap-2 p-1 text-xs cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded">
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes(ev)}
                      onChange={() => toggleEvent(ev)}
                      className="rounded border-neutral-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="font-mono text-[11px] text-neutral-800 dark:text-neutral-200">{ev}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={handleClose}
                className="text-xs px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || selectedEvents.length === 0}
                className="text-xs px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium transition-colors disabled:opacity-50"
              >
                {loading ? "Registering..." : "Register Webhook"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

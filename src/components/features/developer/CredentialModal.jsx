"use client";

import React, { useState } from "react";
import { X, Copy, Check, AlertTriangle, Key } from "lucide-react";
import { developerService } from "@/services/developer";

const AVAILABLE_SCOPES = [
  { id: "tasks:read", label: "tasks:read", desc: "Read tasks and execution plans" },
  { id: "tasks:run", label: "tasks:run", desc: "Execute tasks and start runs" },
  { id: "runs:read", label: "runs:read", desc: "Read runs, outputs, events, and telemetry" },
  { id: "workflows:read", label: "workflows:read", desc: "Read published workflows" },
  { id: "workflows:run", label: "workflows:run", desc: "Execute published workflows" },
  { id: "artifacts:read", label: "artifacts:read", desc: "Read multimodal artifacts" },
  { id: "artifacts:create", label: "artifacts:create", desc: "Create and upload artifacts" },
  { id: "documents:read", label: "documents:read", desc: "Read tenant documents" },
  { id: "memory:read", label: "memory:read", desc: "Read structured memories" },
  { id: "memory:write", label: "memory:write", desc: "Persist new memories" },
  { id: "knowledge:read", label: "knowledge:read", desc: "Read knowledge graph entities" },
  { id: "models:read", label: "models:read", desc: "Query available models and capabilities" },
  { id: "events:read", label: "events:read", desc: "Stream execution lifecycle events" },
  { id: "usage:read", label: "usage:read", desc: "Query API usage and token metrics" },
  { id: "webhooks:manage", label: "webhooks:manage", desc: "Manage callback webhook endpoints" },
];

export function CredentialModal({ isOpen, onClose, applicationId, onCreated }) {
  const [name, setName] = useState("");
  const [selectedScopes, setSelectedScopes] = useState(["tasks:read", "runs:read"]);
  const [expiresInDays, setExpiresInDays] = useState("90");
  const [createdSecret, setCreatedSecret] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  function toggleScope(scopeId) {
    if (selectedScopes.includes(scopeId)) {
      setSelectedScopes(selectedScopes.filter((s) => s !== scopeId));
    } else {
      setSelectedScopes([...selectedScopes, scopeId]);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await developerService.createCredential(applicationId, {
        name: name.trim(),
        scopes: selectedScopes,
        expires_in_days: expiresInDays ? parseInt(expiresInDays, 10) : undefined,
      });
      setCreatedSecret(res.secret_key);
      if (onCreated) onCreated();
    } catch (err) {
      setError(err?.message || "Failed to create credential");
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

  function handleCloseModal() {
    setName("");
    setSelectedScopes(["tasks:read", "runs:read"]);
    setCreatedSecret(null);
    setCopied(false);
    setError(null);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-emerald-500" />
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
              {createdSecret ? "API Credential Generated" : "Generate API Key"}
            </h3>
          </div>
          <button
            onClick={handleCloseModal}
            className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {createdSecret ? (
          <div className="p-5 space-y-4">
            <div className="p-3.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div className="text-xs text-amber-700 dark:text-amber-300">
                <span className="font-semibold">Copy your secret key now.</span> You will not be able to view it again. We store only a cryptographic hash.
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1">
                Plaintext API Key
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
                  className="flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shrink-0 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={handleCloseModal}
                className="text-xs px-4 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 dark:bg-neutral-100 dark:hover:bg-white text-white dark:text-neutral-900 font-medium"
              >
                I have saved my key
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
                Key Label / Name *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., CI/CD Integration Key"
                className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                Expiration
              </label>
              <select
                value={expiresInDays}
                onChange={(e) => setExpiresInDays(e.target.value)}
                className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none"
              >
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90">90 days (Recommended)</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
                <option value="">Never expires</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Permission Scopes
              </label>
              <div className="max-h-48 overflow-y-auto space-y-1.5 p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
                {AVAILABLE_SCOPES.map((sc) => (
                  <label
                    key={sc.id}
                    className="flex items-start gap-2 p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedScopes.includes(sc.id)}
                      onChange={() => toggleScope(sc.id)}
                      className="mt-0.5 rounded border-neutral-300 text-emerald-600 focus:ring-emerald-500"
                    />
                    <div>
                      <div className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                        {sc.label}
                      </div>
                      <div className="text-[11px] text-neutral-500 dark:text-neutral-400">
                        {sc.desc}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={handleCloseModal}
                className="text-xs px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="text-xs px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-colors disabled:opacity-50"
              >
                {loading ? "Generating..." : "Generate Key"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

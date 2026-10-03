"use client";

import React, { useState } from "react";
import { Key, RotateCcw, Trash2, CheckCircle2, AlertCircle, Shield } from "lucide-react";
import { developerService } from "@/services/developer";

export function CredentialTable({ credentials = [], onRefresh, onOpenCreateModal }) {
  const [rotatingId, setRotatingId] = useState(null);
  const [revokingId, setRevokingId] = useState(null);
  const [rotatedSecret, setRotatedSecret] = useState(null);

  async function handleRotate(credId) {
    if (!confirm("Are you sure you want to rotate this credential? A new key will be generated and shown once.")) return;
    setRotatingId(credId);
    try {
      const res = await developerService.rotateCredential(credId);
      setRotatedSecret(res.secret_key);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err?.message || "Failed to rotate credential");
    } finally {
      setRotatingId(null);
    }
  }

  async function handleRevoke(credId) {
    if (!confirm("Revoking this credential will immediately reject all future requests. This action cannot be undone.")) return;
    setRevokingId(credId);
    try {
      await developerService.revokeCredential(credId);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err?.message || "Failed to revoke credential");
    } finally {
      setRevokingId(null);
    }
  }

  return (
    <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm overflow-hidden">
      {rotatedSecret && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border-b border-emerald-200 dark:border-emerald-900 flex items-center justify-between gap-3">
          <div className="text-xs text-emerald-800 dark:text-emerald-200">
            <span className="font-bold">New Secret Key: </span>
            <code className="font-mono bg-white dark:bg-neutral-900 px-2 py-0.5 rounded border border-emerald-300 dark:border-emerald-800 select-all">
              {rotatedSecret}
            </code>
            <span className="ml-2 text-emerald-600 dark:text-emerald-400">(Copy now; will not be shown again)</span>
          </div>
          <button
            onClick={() => setRotatedSecret(null)}
            className="text-xs px-2.5 py-1 rounded bg-emerald-600 text-white font-medium hover:bg-emerald-700"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Key className="w-5 h-5 text-emerald-500" />
          <h3 className="font-semibold text-neutral-900 dark:text-neutral-100">
            API Credentials
          </h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
            {credentials.length}
          </span>
        </div>

        {onOpenCreateModal && (
          <button
            onClick={onOpenCreateModal}
            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
          >
            + Generate Key
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-neutral-50 dark:bg-neutral-800/50 text-neutral-500 dark:text-neutral-400 text-xs border-b border-neutral-200 dark:border-neutral-800">
            <tr>
              <th className="px-4 py-3 font-medium">Key Prefix</th>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Scopes</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Created / Last Used</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
            {credentials.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-neutral-500 dark:text-neutral-400 text-xs">
                  No active credentials. Generate an API key to begin making programmatic requests.
                </td>
              </tr>
            ) : (
              credentials.map((cred) => (
                <tr key={cred.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-neutral-800 dark:text-neutral-200">
                    {cred.key_prefix}...
                  </td>
                  <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100 text-xs">
                    {cred.name}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {(cred.scopes || []).slice(0, 3).map((s, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 font-mono"
                        >
                          {s}
                        </span>
                      ))}
                      {(cred.scopes || []).length > 3 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-500">
                          +{(cred.scopes || []).length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                        cred.status === "active"
                          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                          : cred.status === "rotated"
                          ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
                          : "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
                      }`}
                    >
                      {cred.status === "active" ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : (
                        <AlertCircle className="w-3 h-3" />
                      )}
                      {cred.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-500 dark:text-neutral-400">
                    <div>Created: {new Date(cred.created_at).toLocaleDateString()}</div>
                    <div>Used: {cred.last_used_at ? new Date(cred.last_used_at).toLocaleDateString() : "Never"}</div>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {cred.status !== "revoked" && (
                      <>
                        <button
                          onClick={() => handleRotate(cred.id)}
                          disabled={rotatingId === cred.id}
                          className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 transition-colors"
                          title="Rotate API key"
                        >
                          <RotateCcw className="w-3 h-3" />
                          Rotate
                        </button>
                        <button
                          onClick={() => handleRevoke(cred.id)}
                          disabled={revokingId === cred.id}
                          className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-rose-200 dark:border-rose-900 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-rose-600 dark:text-rose-400 transition-colors"
                          title="Revoke API key"
                        >
                          <Trash2 className="w-3 h-3" />
                          Revoke
                        </button>
                      </>
                    )}
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

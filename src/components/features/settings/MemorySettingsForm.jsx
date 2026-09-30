"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Save,
  RefreshCw,
  Lock,
  Layers,
  Clock,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { memoryService } from "@/services/memory";
import { useWorkspace } from "@/lib/workspaceContext";

export function MemorySettingsForm() {
  const { activeWorkspace } = useWorkspace();
  const [settings, setSettings] = useState({
    memory_enabled: true,
    suggestions_enabled: true,
    default_retrieval_mode: "auto",
    default_memory_scope: "user",
    retention_preference: "never",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Bulk deletion modal
  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    scope: null, // "project" or "workspace"
    isDeleting: false,
  });

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const res = await memoryService.getSettings();
      if (res) {
        setSettings({
          memory_enabled: res.memory_enabled ?? true,
          suggestions_enabled: res.suggestions_enabled ?? true,
          default_retrieval_mode: res.default_retrieval_mode || "auto",
          default_memory_scope: res.default_memory_scope || "user",
          retention_preference: res.retention_preference || "never",
        });
      }
    } catch (err) {
      console.error("[MemorySettings] Error loading settings:", err);
      setErrorMessage(err.message || "Failed to load memory settings");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, [activeWorkspace?.id]);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      setStatusMessage(null);
      setErrorMessage(null);
      await memoryService.updateSettings(settings);
      setStatusMessage("Memory settings updated successfully.");
    } catch (err) {
      setErrorMessage(err.message || "Failed to update memory settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenDeleteModal = (scope) => {
    setConfirmModal({
      isOpen: true,
      scope,
      isDeleting: false,
    });
  };

  const handleConfirmBulkDelete = async () => {
    try {
      setConfirmModal((prev) => ({ ...prev, isDeleting: true }));
      await memoryService.deleteByScope(confirmModal.scope);
      setStatusMessage(`All ${confirmModal.scope} memories were permanently deleted.`);
      setConfirmModal({ isOpen: false, scope: null, isDeleting: false });
    } catch (err) {
      setErrorMessage(err.message || `Failed to delete ${confirmModal.scope} memories`);
      setConfirmModal((prev) => ({ ...prev, isDeleting: false }));
    }
  };

  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <RefreshCw className="w-6 h-6 text-indigo-500 animate-spin mx-auto mb-2" />
        <p className="text-xs text-slate-400">Loading memory configurations...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Notifications */}
      {statusMessage && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-emerald-400 hover:text-emerald-200">
            &times;
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-200">
            &times;
          </button>
        </div>
      )}

      {/* Security Filtering Banner */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex items-start gap-3.5">
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wide">
              Security & Secret Detection Filter
            </h3>
            <Badge variant="outline" className="text-[10px] border-emerald-500/40 text-emerald-300 bg-emerald-500/10">
              Always Active
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            API keys, bearer tokens, private keys, database credentials, passwords, and sensitive PII are automatically
            detected, stripped, or rejected. Security filtering cannot be bypassed or disabled by any user setting.
          </p>
        </div>
      </div>

      {/* Settings Form */}
      <form onSubmit={handleSave} className="space-y-6 bg-slate-900/40 p-6 rounded-xl border border-slate-800/80">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Brain className="w-4 h-4 text-indigo-400" />
            Memory Intelligence & Scope Preferences
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure how the platform retrieves and retains knowledge across your workspaces and tasks.
          </p>
        </div>

        {/* Toggles */}
        <div className="space-y-4 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-xs font-medium text-slate-200 block">Enable Persistent Memory</label>
              <p className="text-[11px] text-slate-400">
                Allow task executions to retrieve relevant persistent memories via ContextEngine.
              </p>
            </div>
            <input
              type="checkbox"
              checked={settings.memory_enabled}
              onChange={(e) => setSettings({ ...settings, memory_enabled: e.target.checked })}
              className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-xs font-medium text-slate-200 block">Allow Memory Suggestions</label>
              <p className="text-[11px] text-slate-400">
                Let the AI identify candidate preferences during tasks and ask for your approval.
              </p>
            </div>
            <input
              type="checkbox"
              checked={settings.suggestions_enabled}
              onChange={(e) => setSettings({ ...settings, suggestions_enabled: e.target.checked })}
              className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
            />
          </div>
        </div>

        {/* Dropdowns */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-800">
          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Default Retrieval Mode</label>
            <select
              value={settings.default_retrieval_mode}
              onChange={(e) => setSettings({ ...settings, default_retrieval_mode: e.target.value })}
              className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="auto">Auto (Bounded hybrid retrieval)</option>
              <option value="always">Always (Include active memories)</option>
              <option value="never">Never (Disable retrieval)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Default Memory Scope</label>
            <select
              value={settings.default_memory_scope}
              onChange={(e) => setSettings({ ...settings, default_memory_scope: e.target.value })}
              className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="user">User (Private to you)</option>
              <option value="workspace">Workspace (All workspace members)</option>
              <option value="project">Project (Inside current project)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Default Retention</label>
            <select
              value={settings.retention_preference}
              onChange={(e) => setSettings({ ...settings, retention_preference: e.target.value })}
              className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="never">Never expire</option>
              <option value="7_days">7 Days</option>
              <option value="30_days">30 Days</option>
              <option value="90_days">90 Days</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-800">
          <Button
            type="submit"
            disabled={isSaving}
            className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm"
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            {isSaving ? "Saving..." : "Save Preferences"}
          </Button>
        </div>
      </form>

      {/* Privacy Controls & Bulk Deletion */}
      <div className="bg-rose-950/20 border border-rose-500/20 p-6 rounded-xl space-y-4">
        <div>
          <h3 className="text-sm font-bold text-rose-300 flex items-center gap-2">
            <Trash2 className="w-4 h-4 text-rose-400" />
            Privacy Controls & Bulk Purge
          </h3>
          <p className="text-xs text-rose-200/70 mt-1">
            Permanently delete groups of memories. This action is irreversible. Private memories of other workspace
            members will never be affected.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleOpenDeleteModal("project")}
            className="text-xs border-rose-500/30 text-rose-300 hover:bg-rose-500/10"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5" />
            Delete All Project Memories
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleOpenDeleteModal("workspace")}
            className="text-xs border-rose-500/30 text-rose-300 hover:bg-rose-500/10"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5" />
            Delete All Workspace Memories
          </Button>
        </div>
      </div>

      {/* Bulk Delete Confirmation Modal */}
      <Modal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, scope: null, isDeleting: false })}
        title={`Confirm Bulk Delete (${confirmModal.scope} scope)`}
      >
        <div className="space-y-4">
          <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-200 text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-300">Irreversible Action Warning</p>
              <p className="mt-1">
                Are you sure you want to permanently delete all <strong>{confirmModal.scope}</strong> memories in this
                workspace? All associated embeddings and conflict records will also be purged.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setConfirmModal({ isOpen: false, scope: null, isDeleting: false })}
              className="text-xs border-slate-800 text-slate-400"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={confirmModal.isDeleting}
              onClick={handleConfirmBulkDelete}
              className="text-xs bg-rose-600 hover:bg-rose-500 text-white font-semibold"
            >
              {confirmModal.isDeleting ? "Deleting..." : `Yes, Delete All ${confirmModal.scope} Memories`}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

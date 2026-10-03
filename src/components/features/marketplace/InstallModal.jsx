"use client";

import React, { useState } from "react";
import {
  X,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Lock,
  Layers,
  Wrench,
  Plug,
  Cpu,
  CheckCircle2,
  Info,
  ArrowRight,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export function InstallModal({ pkg, version, isOpen, onClose, onInstalled }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [workspaceId, setWorkspaceId] = useState("");
  const [configValues, setConfigValues] = useState({});

  if (!isOpen || !pkg) return null;

  const currentVersion = version || pkg.current_version;
  const manifest = currentVersion?.manifest || {};
  const permissions = manifest.permissions || [];
  const dependencies = manifest.dependencies || [];
  const components = manifest.components || [];
  const variables = manifest.configuration?.variables || {};
  const modelRequirements = manifest.compatibility?.model_capabilities || [];

  const handleConfigChange = (key, val) => {
    setConfigValues((prev) => ({ ...prev, [key]: val }));
  };

  const handleInstall = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await marketplaceService.installPackage(pkg.id, {
        package_version_id: currentVersion?.id,
        workspace_id: workspaceId || null,
        configuration: configValues,
      });
      setSuccess(true);
      setTimeout(() => {
        onInstalled?.(res);
        onClose();
      }, 1200);
    } catch (err) {
      setError(err?.message || "Failed to install package. Please check governance policies.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
      <div className="w-full max-w-2xl bg-white dark:bg-neutral-900 rounded-2xl border border-neutral-200 dark:border-neutral-800 shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
              Install Package: {pkg.name}
            </h2>
            <p className="text-xs text-neutral-500 mt-0.5">
              Version: <span className="font-mono font-medium text-neutral-700 dark:text-neutral-300">{currentVersion?.version || "1.0.0"}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs text-neutral-700 dark:text-neutral-300">
          {/* Mandatory Security & Governance Notice */}
          <div className="p-3.5 rounded-xl border border-blue-200 dark:border-blue-900/50 bg-blue-50/60 dark:bg-blue-950/30 flex items-start gap-3">
            <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-blue-900 dark:text-blue-200">
                Security & Authorization Notice
              </p>
              <p className="text-[11px] text-blue-800/80 dark:text-blue-300/80 leading-relaxed">
                Marketplace packages are reusable platform definitions and configurations. Installation does not automatically grant permissions, credentials, or unrestricted access. Existing RBAC and Governance policies remain strictly authoritative during execution.
              </p>
            </div>
          </div>

          {/* Security Status Banner */}
          <div className="flex items-center justify-between p-3 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
            <div className="flex items-center gap-2">
              {currentVersion?.security_status === "scanned" ? (
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
              ) : currentVersion?.security_status === "blocked" ? (
                <ShieldAlert className="w-4 h-4 text-rose-500" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              )}
              <span className="font-medium text-neutral-800 dark:text-neutral-200">
                Security Status:{" "}
                <span className="capitalize">{currentVersion?.security_status || "scanned"}</span>
              </span>
            </div>
            <span className="text-[11px] text-neutral-500">
              SHA-256: {currentVersion?.content_hash?.slice(0, 12)}...
            </span>
          </div>

          {/* Components to be installed */}
          <div>
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-500" />
              Included Components ({components.length})
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {components.map((comp, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded-lg border border-neutral-100 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40"
                >
                  <p className="font-medium text-neutral-800 dark:text-neutral-200 truncate">{comp.name}</p>
                  <p className="text-[10px] text-neutral-400 capitalize">{comp.type?.replace("_", " ")}</p>
                </div>
              ))}
              {components.length === 0 && (
                <p className="text-neutral-400 italic col-span-2">No individual components registered.</p>
              )}
            </div>
          </div>

          {/* Requested Permissions */}
          <div>
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-amber-500" />
              Declared Permissions ({permissions.length})
            </h4>
            <div className="space-y-1.5">
              {permissions.map((perm, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between"
                >
                  <span className="font-mono text-[11px] text-neutral-800 dark:text-neutral-200">{perm.scope}</span>
                  <span className="text-[10px] text-neutral-500">{perm.description || "Required for execution"}</span>
                </div>
              ))}
              {permissions.length === 0 && (
                <p className="text-neutral-400 italic">No extra permissions requested.</p>
              )}
            </div>
          </div>

          {/* Dependencies & Model Requirements */}
          {(dependencies.length > 0 || modelRequirements.length > 0) && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1.5">
                  <Plug className="w-3.5 h-3.5 text-purple-500" />
                  Dependencies ({dependencies.length})
                </h4>
                <div className="space-y-1">
                  {dependencies.map((dep, idx) => (
                    <div key={idx} className="p-1.5 rounded border border-neutral-100 dark:border-neutral-800 text-[11px]">
                      <span className="font-medium text-neutral-800 dark:text-neutral-200">{dep.dependency_identifier}</span>
                      <span className="text-neutral-400 ml-1">({dep.version_constraint || "*"})</span>
                    </div>
                  ))}
                  {dependencies.length === 0 && <p className="text-neutral-400 italic">None</p>}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-emerald-500" />
                  Model Requirements
                </h4>
                <div className="space-y-1">
                  {modelRequirements.map((req, idx) => (
                    <div key={idx} className="p-1.5 rounded border border-neutral-100 dark:border-neutral-800 text-[11px]">
                      <span className="font-mono text-neutral-700 dark:text-neutral-300">{req}</span>
                    </div>
                  ))}
                  {modelRequirements.length === 0 && <p className="text-neutral-400 italic">Standard platform defaults</p>}
                </div>
              </div>
            </div>
          )}

          {/* Configuration Variables */}
          {Object.keys(variables).length > 0 && (
            <div>
              <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-2 flex items-center gap-1.5">
                <Wrench className="w-3.5 h-3.5 text-blue-500" />
                Configuration Variables
              </h4>
              <div className="space-y-2">
                {Object.entries(variables).map(([key, schema]) => (
                  <div key={key} className="space-y-1">
                    <label className="text-[11px] font-medium text-neutral-700 dark:text-neutral-300 flex items-center justify-between">
                      <span>{key} ({schema.type || "string"})</span>
                      {schema.required && <span className="text-rose-500 text-[10px]">Required</span>}
                    </label>
                    <input
                      type={schema.type === "integer" || schema.type === "number" ? "number" : "text"}
                      defaultValue={schema.default !== undefined ? schema.default : ""}
                      onChange={(e) => handleConfigChange(key, e.target.value)}
                      placeholder={schema.description || `Enter ${key}`}
                      className="w-full px-3 py-1.5 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Target Workspace Selector (Optional) */}
          <div>
            <label className="text-[11px] font-medium text-neutral-700 dark:text-neutral-300 block mb-1">
              Target Workspace ID (optional, leave blank for organization-level installation)
            </label>
            <input
              type="text"
              placeholder="e.g. ws_prod_workforce"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
            />
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* Success Banner */}
          {success && (
            <div className="p-3 rounded-lg border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Package installed successfully!
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
          >
            Cancel
          </button>
          <button
            onClick={handleInstall}
            disabled={loading || currentVersion?.security_status === "blocked"}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            {loading ? "Installing..." : "Confirm & Install"}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

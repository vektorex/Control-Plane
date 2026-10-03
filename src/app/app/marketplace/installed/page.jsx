"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Package,
  Layers,
  RefreshCw,
  RotateCcw,
  Trash2,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  Store,
  Clock,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export default function InstalledPackagesPage() {
  const [installations, setInstallations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchInstallations = async () => {
    setLoading(true);
    try {
      const res = await marketplaceService.listInstallations();
      setInstallations(res?.installations || []);
    } catch (err) {
      setError(err?.message || "Failed to load installed packages.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstallations();
  }, []);

  const handleUninstall = async (installationId, name) => {
    if (!confirm(`Are you sure you want to uninstall ${name || "this package"}?`)) return;
    try {
      await marketplaceService.uninstall(installationId);
      fetchInstallations();
    } catch (err) {
      alert("Uninstall failed: " + err.message);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-500" />
            Installed Packages & Workspace Extensions
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Manage active package installations, version updates, rollbacks, and configuration bindings across your workspaces.
          </p>
        </div>

        <Link
          href="/app/marketplace"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
        >
          <Store className="w-3.5 h-3.5" />
          Browse Marketplace
        </Link>
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-16 text-center text-neutral-500">
          <RotateCcw className="w-6 h-6 animate-spin mx-auto text-blue-500 mb-2" />
          <p className="text-xs">Loading installed packages...</p>
        </div>
      ) : installations.length === 0 ? (
        <div className="p-16 text-center border border-dashed rounded-2xl border-neutral-300 dark:border-neutral-800 space-y-3">
          <Package className="w-8 h-8 text-neutral-400 mx-auto" />
          <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
            No packages currently installed
          </p>
          <p className="text-xs text-neutral-400 max-w-md mx-auto">
            Discover workflow templates, evaluation datasets, and complete work packs in the marketplace.
          </p>
          <Link
            href="/app/marketplace"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
          >
            <Store className="w-3.5 h-3.5" />
            Explore Marketplace
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {installations.map((inst) => {
            const pkg = inst.package || {};
            const version = inst.package_version || {};
            const isUpdateAvailable = inst.status === "update_available";

            return (
              <div
                key={inst.id}
                className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span
                      className={`capitalize text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        inst.status === "installed"
                          ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400"
                          : inst.status === "update_available"
                          ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400"
                          : inst.status === "blocked"
                          ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400"
                          : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600"
                      }`}
                    >
                      {inst.status?.replace("_", " ")}
                    </span>
                    <span className="font-mono text-xs text-neutral-400">
                      v{version.version || "1.0.0"}
                    </span>
                  </div>

                  <Link
                    href={`/app/marketplace/installed/${inst.id}`}
                    className="block group"
                  >
                    <h3 className="text-base font-bold text-neutral-900 dark:text-neutral-100 group-hover:text-blue-600 transition-colors">
                      {pkg.name || "Workflow Package"}
                    </h3>
                    <p className="text-xs text-neutral-400 font-mono mt-0.5">{pkg.slug}</p>
                  </Link>

                  <p className="text-xs text-neutral-500 mt-2 line-clamp-2">
                    {pkg.description || "Installed workflow package."}
                  </p>

                  <div className="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-800/80 text-[11px] text-neutral-400 space-y-1">
                    <p>
                      Workspace: <span className="text-neutral-700 dark:text-neutral-300 font-medium">{inst.workspace_id || "Organization Default"}</span>
                    </p>
                    <p>
                      Installed: {new Date(inst.installed_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-neutral-100 dark:border-neutral-800">
                  <button
                    onClick={() => handleUninstall(inst.id, pkg.name)}
                    className="text-xs text-rose-600 dark:text-rose-400 hover:text-rose-700 flex items-center gap-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Uninstall
                  </button>

                  <Link
                    href={`/app/marketplace/installed/${inst.id}`}
                    className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 transition-colors"
                  >
                    Manage
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

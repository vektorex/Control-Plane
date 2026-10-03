"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Package,
  Layers,
  Lock,
  Wrench,
  RefreshCw,
  RotateCcw,
  Trash2,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Info,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";
import { UpdateModal } from "@/components/features/marketplace/UpdateModal";
import { RollbackModal } from "@/components/features/marketplace/RollbackModal";

export default function InstallationDetailPage({ params }) {
  const router = useRouter();
  const unwrappedParams = use(params);
  const installationId = unwrappedParams.installationId;

  const [installation, setInstallation] = useState(null);
  const [packageVersions, setPackageVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals
  const [isUpdateOpen, setIsUpdateOpen] = useState(false);
  const [isRollbackOpen, setIsRollbackOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const instData = await marketplaceService.getInstallation(installationId);
      setInstallation(instData);

      if (instData?.package_id) {
        const verData = await marketplaceService.listVersions(instData.package_id);
        setPackageVersions(verData?.versions || []);
      }
    } catch (err) {
      setError(err?.message || "Failed to load installation details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (installationId) {
      loadData();
    }
  }, [installationId]);

  const handleUninstall = async () => {
    if (!confirm("Are you sure you want to uninstall this package from your workspace?")) return;
    try {
      await marketplaceService.uninstall(installationId);
      router.push("/app/marketplace/installed");
    } catch (err) {
      alert("Uninstall failed: " + err.message);
    }
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-neutral-500 text-xs">
        Loading installation details...
      </div>
    );
  }

  if (error || !installation) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs">
          {error || "Installation not found."}
        </div>
        <Link href="/app/marketplace/installed" className="text-xs text-blue-600 hover:underline">
          ← Return to Installed Packages
        </Link>
      </div>
    );
  }

  const pkg = installation.package || {};
  const currentVersion = installation.package_version || {};
  const manifest = currentVersion.manifest || {};
  const components = manifest.components || [];
  const permissions = manifest.permissions || [];
  const configuration = installation.configuration || {};

  // Check if a newer published version is available
  const latestPublishedVersion = packageVersions.find(
    (v) => v.publication_status === "published" && v.id !== installation.package_version_id
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-neutral-400">
        <Link href="/app/marketplace" className="hover:text-neutral-600 dark:hover:text-neutral-200">
          Marketplace
        </Link>
        <span>/</span>
        <Link href="/app/marketplace/installed" className="hover:text-neutral-600 dark:hover:text-neutral-200">
          Installed Packages
        </Link>
        <span>/</span>
        <span className="text-neutral-700 dark:text-neutral-300 font-mono">{installation.id}</span>
      </div>

      {/* Header Card */}
      <div className="p-6 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {pkg.name || "Installed Package"}
              </h1>
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-900/50">
                v{currentVersion.version || "1.0.0"}
              </span>
              <span
                className={`capitalize text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                  installation.status === "installed"
                    ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400"
                    : installation.status === "update_available"
                    ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400"
                    : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600"
                }`}
              >
                {installation.status?.replace("_", " ")}
              </span>
            </div>
            <p className="text-xs text-neutral-500">
              Workspace Scope: <span className="font-medium text-neutral-800 dark:text-neutral-200">{installation.workspace_id || "Organization Default"}</span> • Installed on {new Date(installation.installed_at).toLocaleString()}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {latestPublishedVersion && (
              <button
                onClick={() => setIsUpdateOpen(true)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 text-white font-semibold text-xs hover:bg-blue-700 transition-colors shadow-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Update to v{latestPublishedVersion.version}
              </button>
            )}

            <button
              onClick={() => setIsRollbackOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700 text-xs font-medium text-neutral-800 dark:text-neutral-200 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-amber-500" />
              Rollback
            </button>

            <button
              onClick={handleUninstall}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-rose-200 dark:border-rose-900/40 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-xs font-medium transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Uninstall
            </button>
          </div>
        </div>
      </div>

      {/* Grid: Manifest Components & Config Values */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-xs">
        {/* Components */}
        <div className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-blue-500" />
            Installed Components ({components.length})
          </h3>
          <div className="space-y-2">
            {components.map((c, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-neutral-100 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between"
              >
                <div>
                  <span className="font-semibold text-neutral-800 dark:text-neutral-200">
                    {c.name}
                  </span>
                  <span className="text-[10px] text-neutral-400 ml-2 capitalize">
                    ({c.type?.replace("_", " ")})
                  </span>
                </div>
                <span className="font-mono text-neutral-500 text-[11px]">{c.identifier}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration Values */}
        <div className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
            <Wrench className="w-4 h-4 text-amber-500" />
            Active Workspace Configuration
          </h3>
          {Object.keys(configuration).length === 0 ? (
            <p className="text-neutral-400 italic">No custom configuration overrides applied.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(configuration).map(([k, v]) => (
                <div
                  key={k}
                  className="p-3 rounded-xl border border-neutral-100 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between"
                >
                  <span className="font-mono font-medium text-neutral-700 dark:text-neutral-300">{k}</span>
                  <span className="font-mono text-neutral-900 dark:text-neutral-100">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Permissions Box */}
      <div className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-3 text-xs">
        <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
          <Lock className="w-4 h-4 text-purple-500" />
          Declared Execution Permissions ({permissions.length})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {permissions.map((p, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl border border-neutral-100 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 space-y-1"
            >
              <p className="font-mono font-bold text-neutral-800 dark:text-neutral-200">{p.scope}</p>
              <p className="text-[10px] text-neutral-400">{p.description || "Operational permission"}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Modals */}
      {latestPublishedVersion && (
        <UpdateModal
          installation={installation}
          newVersion={latestPublishedVersion}
          isOpen={isUpdateOpen}
          onClose={() => setIsUpdateOpen(false)}
          onUpdated={loadData}
        />
      )}

      <RollbackModal
        installation={installation}
        versions={packageVersions}
        isOpen={isRollbackOpen}
        onClose={() => setIsRollbackOpen(false)}
        onRolledBack={loadData}
      />
    </div>
  );
}

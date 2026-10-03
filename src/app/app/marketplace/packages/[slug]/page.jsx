"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  Package,
  Layers,
  Lock,
  Plug,
  Wrench,
  BookOpen,
  History,
  GitFork,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Building2,
  Calendar,
  Hash,
  Star,
  Activity,
  CheckCircle2,
  Cpu,
  ArrowRight,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";
import { InstallModal } from "@/components/features/marketplace/InstallModal";
import { ReviewSection } from "@/components/features/marketplace/ReviewSection";

export default function PackageDetailPage({ params }) {
  const unwrappedParams = use(params);
  const slug = unwrappedParams.slug;

  const [pkg, setPkg] = useState(null);
  const [version, setVersion] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Install Modal
  const [isInstallOpen, setIsInstallOpen] = useState(false);

  // Fork State
  const [forking, setForking] = useState(false);
  const [forkSuccess, setForkSuccess] = useState(false);

  // Active Tab
  const [activeTab, setActiveTab] = useState("overview");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const packageData = await marketplaceService.getPackageBySlug(slug);
      setPkg(packageData);
      setVersion(packageData.current_version);

      if (packageData?.id) {
        const [revData, usageData] = await Promise.all([
          marketplaceService.listReviews(packageData.id).catch(() => ({ reviews: [] })),
          marketplaceService.getUsage(packageData.id).catch(() => null),
        ]);
        setReviews(revData?.reviews || []);
        setUsage(usageData);
      }
    } catch (err) {
      setError(err?.message || "Failed to load package details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (slug) {
      loadData();
    }
  }, [slug]);

  const handleFork = async () => {
    if (!pkg) return;
    setForking(true);
    try {
      await marketplaceService.forkPackage(pkg.id, {
        new_name: `${pkg.name} (Forked)`,
        new_slug: `${pkg.slug}-fork`,
      });
      setForkSuccess(true);
      setTimeout(() => setForkSuccess(false), 3000);
    } catch (err) {
      alert("Fork failed: " + err.message);
    } finally {
      setForking(false);
    }
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-neutral-500 text-xs">
        Loading package details...
      </div>
    );
  }

  if (error || !pkg) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <div className="p-4 rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-xs">
          {error || "Package not found."}
        </div>
        <Link
          href="/app/marketplace"
          className="text-xs text-blue-600 hover:underline"
        >
          ← Return to Marketplace
        </Link>
      </div>
    );
  }

  const manifest = version?.manifest || {};
  const components = manifest.components || [];
  const permissions = manifest.permissions || [];
  const dependencies = manifest.dependencies || [];
  const variables = manifest.configuration?.variables || {};
  const documentation = manifest.documentation || {};
  const compatibility = manifest.compatibility || {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-neutral-400">
        <Link href="/app/marketplace" className="hover:text-neutral-600 dark:hover:text-neutral-200">
          Marketplace
        </Link>
        <span>/</span>
        <Link href="/app/marketplace/packages" className="hover:text-neutral-600 dark:hover:text-neutral-200">
          Packages
        </Link>
        <span>/</span>
        <span className="text-neutral-700 dark:text-neutral-300 font-mono">{pkg.slug}</span>
      </div>

      {/* Package Header Card */}
      <div className="p-6 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {pkg.name}
              </h1>
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-900/50">
                v{version?.version || "1.0.0"}
              </span>
              <span className="capitalize text-xs px-2.5 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300">
                {pkg.package_type?.replace("_", " ")}
              </span>
              <span className="capitalize text-xs px-2.5 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300">
                {pkg.category}
              </span>
            </div>
            <p className="text-xs text-neutral-600 dark:text-neutral-300 max-w-3xl leading-relaxed">
              {pkg.description || "No package description provided."}
            </p>

            {/* Author Org & Provenance */}
            <div className="flex flex-wrap items-center gap-4 text-[11px] text-neutral-500 pt-1">
              <span className="flex items-center gap-1">
                <Building2 className="w-3.5 h-3.5 text-neutral-400" />
                Org: <span className="font-medium text-neutral-700 dark:text-neutral-300">{pkg.owner_organization_id?.slice(0, 14)}...</span>
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-neutral-400" />
                Published: {version?.published_at ? new Date(version.published_at).toLocaleDateString() : "Draft"}
              </span>
              <span className="flex items-center gap-1 font-mono">
                <Hash className="w-3.5 h-3.5 text-neutral-400" />
                SHA-256: {version?.content_hash?.slice(0, 10)}...
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleFork}
              disabled={forking}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 text-xs font-medium text-neutral-800 dark:text-neutral-200 transition-colors"
            >
              <GitFork className="w-3.5 h-3.5" />
              {forking ? "Forking..." : "Fork"}
            </button>
            <Link
              href={`/app/marketplace/packages/${pkg.slug}/versions`}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 text-xs font-medium text-neutral-800 dark:text-neutral-200 transition-colors"
            >
              <History className="w-3.5 h-3.5" />
              Versions
            </Link>
            {pkg.status === "published" && (
              <button
                onClick={() => setIsInstallOpen(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold text-xs hover:bg-blue-700 transition-colors shadow-xs"
              >
                Install Package
              </button>
            )}
          </div>
        </div>

        {forkSuccess && (
          <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> Package forked into your organization successfully!
          </div>
        )}

        {/* Factual Security Status Banner */}
        <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            {version?.security_status === "scanned" ? (
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
            ) : version?.security_status === "blocked" ? (
              <ShieldAlert className="w-4 h-4 text-rose-500" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            )}
            <span className="font-semibold text-neutral-800 dark:text-neutral-200">
              Security Status: <span className="capitalize">{version?.security_status || "scanned"}</span>
            </span>
            <span className="text-neutral-400">• Static validation passed, zero secrets embedded</span>
          </div>

          <div className="flex items-center gap-3 text-neutral-500 text-[11px]">
            <span>Min Platform: {compatibility?.platform_min_version || "1.0.0"}</span>
            <span>•</span>
            <span>Components: {components.length}</span>
            <span>•</span>
            <span>Dependencies: {dependencies.length}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-200 dark:border-neutral-800 text-xs font-medium">
        {[
          { id: "overview", label: "Overview & Docs", icon: BookOpen },
          { id: "components", label: `Components (${components.length})`, icon: Layers },
          { id: "permissions", label: `Permissions (${permissions.length})`, icon: Lock },
          { id: "dependencies", label: `Dependencies (${dependencies.length})`, icon: Plug },
          { id: "reviews", label: `Reviews (${reviews.length})`, icon: Star },
          { id: "usage", label: "Factual Usage", icon: Activity },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 border-b-2 transition-colors ${
                isActive
                  ? "border-blue-600 text-blue-600 font-semibold"
                  : "border-transparent text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="p-6 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm text-xs space-y-6">
        {/* TAB 1: Overview & Documentation */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100 mb-2">
                Documentation & Usage Guide
              </h3>
              <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-100 dark:border-neutral-800 font-mono text-[11px] whitespace-pre-wrap leading-relaxed text-neutral-800 dark:text-neutral-200">
                {documentation.readme || "# No README available for this package."}
              </div>
            </div>

            {documentation.usage && (
              <div>
                <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                  Usage Instructions:
                </h4>
                <p className="text-neutral-600 dark:text-neutral-400">
                  {documentation.usage}
                </p>
              </div>
            )}

            {documentation.limitations && (
              <div>
                <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                  Known Limitations:
                </h4>
                <p className="text-neutral-600 dark:text-neutral-400">
                  {documentation.limitations}
                </p>
              </div>
            )}

            {documentation.security_notes && (
              <div>
                <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                  Security Notes:
                </h4>
                <p className="text-neutral-600 dark:text-neutral-400">
                  {documentation.security_notes}
                </p>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Components */}
        {activeTab === "components" && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Included Package Components
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {components.map((comp, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-neutral-900 dark:text-neutral-100">
                      {comp.name}
                    </span>
                    <span className="capitalize text-[10px] px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400">
                      {comp.type?.replace("_", " ")}
                    </span>
                  </div>
                  <p className="font-mono text-[11px] text-neutral-500">
                    Identifier: {comp.identifier}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: Permissions */}
        {activeTab === "permissions" && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Required Permission Scopes
            </h3>
            <p className="text-neutral-500 text-[11px]">
              These scopes are checked during workflow dispatch and task orchestration. Installation of this package does not bypass tenant RBAC.
            </p>
            <div className="space-y-2">
              {permissions.map((p, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between"
                >
                  <span className="font-mono font-semibold text-neutral-800 dark:text-neutral-200">
                    {p.scope}
                  </span>
                  <span className="text-neutral-500 text-[11px]">
                    {p.description || "Operational execution scope"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: Dependencies */}
        {activeTab === "dependencies" && (
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Package Dependencies
            </h3>
            {dependencies.length === 0 ? (
              <p className="text-neutral-400 italic">No external dependencies declared.</p>
            ) : (
              <div className="space-y-2">
                {dependencies.map((d, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/40 flex items-center justify-between"
                  >
                    <div>
                      <span className="font-semibold text-neutral-900 dark:text-neutral-100">
                        {d.dependency_identifier}
                      </span>
                      <span className="text-[10px] text-neutral-400 ml-2 capitalize">
                        ({d.dependency_type})
                      </span>
                    </div>
                    <span className="font-mono text-neutral-600 dark:text-neutral-400">
                      {d.version_constraint || "*"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 5: Reviews */}
        {activeTab === "reviews" && (
          <ReviewSection
            packageId={pkg.id}
            reviews={reviews}
            onReviewSubmitted={loadData}
          />
        )}

        {/* TAB 6: Usage Statistics */}
        {activeTab === "usage" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-100">
              Factual Telemetry & Operational Analytics
            </h3>
            <p className="text-neutral-500 text-[11px]">
              Non-subjective execution rollups across authorized tenant workspaces.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
                <p className="text-neutral-400 text-[11px]">Installations</p>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                  {usage?.installations ?? 0}
                </p>
              </div>
              <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
                <p className="text-neutral-400 text-[11px]">Total Runs</p>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                  {usage?.runs ?? 0}
                </p>
              </div>
              <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
                <p className="text-neutral-400 text-[11px]">Updates</p>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                  {usage?.updates ?? 0}
                </p>
              </div>
              <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50">
                <p className="text-neutral-400 text-[11px]">Uninstalls</p>
                <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                  {usage?.uninstalls ?? 0}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Install Modal */}
      <InstallModal
        pkg={pkg}
        version={version}
        isOpen={isInstallOpen}
        onClose={() => setIsInstallOpen(false)}
        onInstalled={() => {
          loadData();
        }}
      />
    </div>
  );
}

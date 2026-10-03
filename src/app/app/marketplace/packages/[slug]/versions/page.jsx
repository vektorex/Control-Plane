"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  History,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Calendar,
  Hash,
  ArrowLeft,
  Ban,
  Archive,
  RotateCcw,
  CheckCircle2,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export default function PackageVersionsPage({ params }) {
  const unwrappedParams = use(params);
  const slug = unwrappedParams.slug;

  const [pkg, setPkg] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [revokingId, setRevokingId] = useState(null);
  const [revokeReason, setRevokeReason] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const packageData = await marketplaceService.getPackageBySlug(slug);
      setPkg(packageData);
      if (packageData?.id) {
        const verData = await marketplaceService.listVersions(packageData.id);
        setVersions(verData?.versions || []);
      }
    } catch (err) {
      setError(err?.message || "Failed to load versions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (slug) {
      loadData();
    }
  }, [slug]);

  const handleDeprecate = async (versionId) => {
    if (!confirm("Are you sure you want to mark this version as deprecated?")) return;
    try {
      await marketplaceService.deprecateVersion(pkg.id, versionId);
      loadData();
    } catch (err) {
      alert("Deprecation failed: " + err.message);
    }
  };

  const handleRevoke = async (versionId) => {
    if (!revokeReason.trim()) {
      alert("Please provide a reason for revoking this version.");
      return;
    }
    try {
      await marketplaceService.revokeVersion(pkg.id, versionId, revokeReason);
      setRevokingId(null);
      setRevokeReason("");
      loadData();
    } catch (err) {
      alert("Revocation failed: " + err.message);
    }
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-neutral-500 text-xs">
        Loading package versions...
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-neutral-400">
        <Link href="/app/marketplace" className="hover:text-neutral-600 dark:hover:text-neutral-200">
          Marketplace
        </Link>
        <span>/</span>
        <Link href={`/app/marketplace/packages/${slug}`} className="hover:text-neutral-600 dark:hover:text-neutral-200">
          {pkg?.name || slug}
        </Link>
        <span>/</span>
        <span className="text-neutral-700 dark:text-neutral-300">Version History</span>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <History className="w-5 h-5 text-blue-500" />
            Immutable Version History: {pkg?.name}
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Published versions are immutable. New capabilities require publishing a new semantic version.
          </p>
        </div>

        <Link
          href={`/app/marketplace/packages/${slug}`}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Package
        </Link>
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-xs">
          {error}
        </div>
      )}

      {/* Version List */}
      <div className="space-y-4">
        {versions.map((ver) => (
          <div
            key={ver.id}
            className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-xs space-y-3 text-xs"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-base font-bold text-neutral-900 dark:text-neutral-100">
                  v{ver.version}
                </span>
                <span
                  className={`capitalize px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                    ver.publication_status === "published"
                      ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400"
                      : ver.publication_status === "deprecated"
                      ? "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400"
                      : ver.publication_status === "revoked"
                      ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400"
                      : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600"
                  }`}
                >
                  {ver.publication_status}
                </span>
                <span className="flex items-center gap-1 text-[11px] text-neutral-500">
                  {ver.security_status === "scanned" ? (
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                  ) : ver.security_status === "blocked" ? (
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  )}
                  {ver.security_status}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {ver.publication_status === "published" && (
                  <>
                    <button
                      onClick={() => handleDeprecate(ver.id)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded border border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 text-[11px]"
                    >
                      <Archive className="w-3 h-3 text-amber-500" /> Deprecate
                    </button>
                    <button
                      onClick={() => setRevokingId(ver.id)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded border border-rose-200 dark:border-rose-900/40 text-rose-600 dark:text-rose-400 hover:bg-rose-50 text-[11px]"
                    >
                      <Ban className="w-3 h-3" /> Revoke
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Revoke confirmation box */}
            {revokingId === ver.id && (
              <div className="p-3 rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20 space-y-2">
                <p className="font-semibold text-rose-900 dark:text-rose-200">
                  Revoke Version v{ver.version} (Security Incident or Severe Defect)
                </p>
                <input
                  type="text"
                  placeholder="Enter reason for revocation..."
                  value={revokeReason}
                  onChange={(e) => setRevokeReason(e.target.value)}
                  className="w-full px-3 py-1.5 rounded border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-xs"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setRevokingId(null)}
                    className="px-2.5 py-1 text-[11px] text-neutral-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleRevoke(ver.id)}
                    className="px-3 py-1 rounded bg-rose-600 text-white font-semibold text-[11px]"
                  >
                    Confirm Revocation
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] text-neutral-500 pt-2 border-t border-neutral-100 dark:border-neutral-800">
              <span className="flex items-center gap-1 font-mono">
                <Hash className="w-3 h-3 text-neutral-400" />
                Hash: {ver.content_hash?.slice(0, 16)}...
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-neutral-400" />
                Created: {new Date(ver.created_at).toLocaleString()}
              </span>
              <span>
                Components: {ver.manifest?.components?.length || 0} • Permissions: {ver.manifest?.permissions?.length || 0}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

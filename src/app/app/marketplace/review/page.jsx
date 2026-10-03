"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Lock,
  ArrowRight,
  Package,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export default function MarketplaceGovernanceReviewPage() {
  const [packagesInReview, setPackagesInReview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewNote, setReviewNote] = useState("");
  const [selectedPkg, setSelectedPkg] = useState(null);

  const fetchReviewQueue = async () => {
    setLoading(true);
    try {
      const res = await marketplaceService.listPackages({
        status: "review",
        limit: 50,
      });
      setPackagesInReview(res?.packages || res?.items || []);
    } catch (err) {
      console.error("Failed to load packages in review", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviewQueue();
  }, []);

  const handleApprove = async (pkg) => {
    if (!confirm(`Approve publication of package: ${pkg.name}?`)) return;
    setActionLoading(true);
    try {
      // If version is pending, publish it
      if (pkg.current_version_id) {
        await marketplaceService.publishVersion(pkg.id, pkg.current_version_id);
      }
      fetchReviewQueue();
      setSelectedPkg(null);
    } catch (err) {
      alert("Approval failed: " + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (pkg) => {
    if (!confirm(`Reject publication of package: ${pkg.name}?`)) return;
    setActionLoading(true);
    try {
      await marketplaceService.updatePackage(pkg.id, {
        status: "draft",
      });
      fetchReviewQueue();
      setSelectedPkg(null);
    } catch (err) {
      alert("Rejection failed: " + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-500" />
          Marketplace Governance & HITL Review Queue
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          Review packages requesting public marketplace publication, sensitive permissions, or external integrations.
        </p>
      </div>

      {loading ? (
        <div className="p-16 text-center text-xs text-neutral-500">
          Loading governance review queue...
        </div>
      ) : packagesInReview.length === 0 ? (
        <div className="p-16 text-center border border-dashed rounded-2xl border-neutral-300 dark:border-neutral-800 space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
          <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-200">
            Review Queue Clear
          </p>
          <p className="text-xs text-neutral-400">
            No packages currently awaiting administrator governance review.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {packagesInReview.map((pkg) => (
            <div
              key={pkg.id}
              className="p-5 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-neutral-900 dark:text-neutral-100 text-sm">
                    {pkg.name}
                  </span>
                  <span className="font-mono text-neutral-400 text-[11px]">
                    ({pkg.slug})
                  </span>
                  <span className="capitalize px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400">
                    Awaiting Approval
                  </span>
                </div>
                <p className="text-neutral-600 dark:text-neutral-300">
                  {pkg.description || "No description."}
                </p>
                <div className="flex items-center gap-4 text-[11px] text-neutral-400 pt-1">
                  <span>Type: <span className="capitalize text-neutral-700 dark:text-neutral-300">{pkg.package_type?.replace("_", " ")}</span></span>
                  <span>Category: <span className="capitalize text-neutral-700 dark:text-neutral-300">{pkg.category}</span></span>
                  <span>Requested Visibility: <span className="capitalize text-neutral-700 dark:text-neutral-300">{pkg.visibility}</span></span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  href={`/app/marketplace/packages/${pkg.slug}`}
                  className="px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 font-medium hover:bg-neutral-50 dark:hover:bg-neutral-800"
                >
                  Inspect
                </Link>
                <button
                  onClick={() => handleReject(pkg)}
                  disabled={actionLoading}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-rose-200 dark:border-rose-900/40 text-rose-600 dark:text-rose-400 hover:bg-rose-50 font-medium"
                >
                  <XCircle className="w-3.5 h-3.5" /> Reject
                </button>
                <button
                  onClick={() => handleApprove(pkg)}
                  disabled={actionLoading}
                  className="flex items-center gap-1 px-4 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 shadow-xs"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Publish
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

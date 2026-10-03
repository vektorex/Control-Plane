"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { Plus, ArrowLeft } from "lucide-react";
import { marketplaceService } from "@/services/marketplace";
import { PackageCreatorWizard } from "@/components/features/marketplace/PackageCreatorWizard";

export default function PackageEditPage({ params }) {
  const unwrappedParams = use(params);
  const packageId = unwrappedParams.packageId;

  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await marketplaceService.getPackage(packageId);
        setPkg(data);
      } catch (err) {
        console.error("Failed to load package for edit", err);
      } finally {
        setLoading(false);
      }
    }
    if (packageId) {
      load();
    }
  }, [packageId]);

  if (loading) {
    return <div className="p-16 text-center text-xs text-neutral-500">Loading package...</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <Plus className="w-5 h-5 text-blue-500" />
            Manage Package Version: {pkg?.name || packageId}
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Publish a new immutable version for this workflow package.
          </p>
        </div>

        <Link
          href={`/app/marketplace/packages/${pkg?.slug || ""}`}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back
        </Link>
      </div>

      <PackageCreatorWizard existingPackage={pkg} />
    </div>
  );
}

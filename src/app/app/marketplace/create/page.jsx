"use client";

import React from "react";
import Link from "next/link";
import { Plus, ArrowLeft } from "lucide-react";
import { PackageCreatorWizard } from "@/components/features/marketplace/PackageCreatorWizard";

export default function PackageCreatePage() {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <Plus className="w-5 h-5 text-blue-500" />
            Create Reusable Workflow Package
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Build, configure, validate, and publish a reusable AI Work Layer package with strict schema boundaries.
          </p>
        </div>

        <Link
          href="/app/marketplace"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Marketplace
        </Link>
      </div>

      <PackageCreatorWizard />
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Store,
  Package,
  Layers,
  Sparkles,
  ShieldCheck,
  Plus,
  Terminal,
  Clock,
  ArrowRight,
  RotateCcw,
} from "lucide-react";
import { marketplaceService } from "@/services/marketplace";
import { PackageCard } from "@/components/features/marketplace/PackageCard";
import { PackageFilters } from "@/components/features/marketplace/PackageFilters";
import { InstallModal } from "@/components/features/marketplace/InstallModal";

export default function MarketplaceHomePage() {
  const [packages, setPackages] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [packageType, setPackageType] = useState("");
  const [visibility, setVisibility] = useState("");

  // Modal
  const [selectedPkg, setSelectedPkg] = useState(null);
  const [isInstallOpen, setIsInstallOpen] = useState(false);

  const fetchPackages = async () => {
    setLoading(true);
    try {
      const [pkgsRes, catsRes] = await Promise.all([
        marketplaceService.listPackages({
          query: search || undefined,
          category: category || undefined,
          package_type: packageType || undefined,
          visibility: visibility || undefined,
          limit: 30,
        }),
        marketplaceService.getCategories().catch(() => ({ categories: [] })),
      ]);
      setPackages(pkgsRes?.items || pkgsRes?.packages || []);
      setCategories(catsRes?.categories || []);
    } catch (err) {
      console.error("Failed to load marketplace packages", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, [category, packageType, visibility]);

  const handleSearchSubmit = (e) => {
    e?.preventDefault();
    fetchPackages();
  };

  const handleInstallClick = (pkg) => {
    setSelectedPkg(pkg);
    setIsInstallOpen(true);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Top Banner & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Store className="w-6 h-6 text-blue-500" />
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              AI Workflow Marketplace & Extension Ecosystem
            </h1>
          </div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Discover, validate, publish, and install versioned AI workflow templates, prompt packs, and tool definitions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/marketplace/installed"
            className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 text-neutral-800 dark:text-neutral-200 transition-colors"
          >
            <Clock className="w-3.5 h-3.5" />
            Installed Packages
          </Link>
          <Link
            href="/app/marketplace/sandbox"
            className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 text-neutral-800 dark:text-neutral-200 transition-colors"
          >
            <Terminal className="w-3.5 h-3.5" />
            Sandbox
          </Link>
          <Link
            href="/app/marketplace/create"
            className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            Create Package
          </Link>
        </div>
      </div>

      {/* Mandatory Governance & Zero-Trust Notice */}
      <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/40 bg-blue-50/50 dark:bg-blue-950/20 flex items-start gap-3 text-xs">
        <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-semibold text-blue-900 dark:text-blue-200">
            Platform Security & Untrusted Package Sandboxing
          </p>
          <p className="text-[11px] text-blue-800/80 dark:text-blue-300/80 leading-relaxed">
            Marketplace packages are reusable platform definitions and configurations. Installation does not automatically grant permissions, credentials, or unrestricted access. All packages are subject to deterministic schema validation, static security scanning, and tenant-scoped governance policies.
          </p>
        </div>
      </div>

      {/* Search & Filters */}
      <form onSubmit={handleSearchSubmit}>
        <PackageFilters
          search={search}
          setSearch={setSearch}
          category={category}
          setCategory={setCategory}
          packageType={packageType}
          setPackageType={setPackageType}
          visibility={visibility}
          setVisibility={setVisibility}
          categories={categories}
          onReset={() => {
            setSearch("");
            setCategory("");
            setPackageType("");
            setVisibility("");
            fetchPackages();
          }}
        />
      </form>

      {/* Package Grid */}
      {loading ? (
        <div className="p-16 text-center text-neutral-500 space-y-2">
          <RotateCcw className="w-6 h-6 animate-spin mx-auto text-blue-500" />
          <p className="text-xs">Loading marketplace catalog...</p>
        </div>
      ) : packages.length === 0 ? (
        <div className="p-16 text-center border border-dashed rounded-2xl border-neutral-300 dark:border-neutral-800 space-y-3">
          <Package className="w-8 h-8 text-neutral-400 mx-auto" />
          <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
            No marketplace packages found
          </p>
          <p className="text-xs text-neutral-400 max-w-md mx-auto">
            Try adjusting your search criteria or create your organization&apos;s first reusable workflow package.
          </p>
          <Link
            href="/app/marketplace/create"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            Create Package
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {packages.map((pkg) => (
            <PackageCard
              key={pkg.id}
              pkg={pkg}
              onInstallClick={handleInstallClick}
            />
          ))}
        </div>
      )}

      {/* Install Modal */}
      {selectedPkg && (
        <InstallModal
          pkg={selectedPkg}
          isOpen={isInstallOpen}
          onClose={() => {
            setIsInstallOpen(false);
            setSelectedPkg(null);
          }}
          onInstalled={() => {
            fetchPackages();
          }}
        />
      )}
    </div>
  );
}

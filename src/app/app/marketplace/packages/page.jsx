"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Store, Package, Plus, RotateCcw } from "lucide-react";
import { marketplaceService } from "@/services/marketplace";
import { PackageCard } from "@/components/features/marketplace/PackageCard";
import { PackageFilters } from "@/components/features/marketplace/PackageFilters";
import { InstallModal } from "@/components/features/marketplace/InstallModal";

export default function MarketplaceDirectoryPage() {
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
          limit: 50,
        }),
        marketplaceService.getCategories().catch(() => ({ categories: [] })),
      ]);
      setPackages(pkgsRes?.items || pkgsRes?.packages || []);
      setCategories(catsRes?.categories || []);
    } catch (err) {
      console.error("Failed to load packages directory", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, [category, packageType, visibility]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-500" />
            Marketplace Package Directory
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Browse all verified and organization-scoped templates, workflows, tools, and work packs.
          </p>
        </div>

        <Link
          href="/app/marketplace/create"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-xs"
        >
          <Plus className="w-3.5 h-3.5" />
          Create Package
        </Link>
      </div>

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

      {loading ? (
        <div className="p-16 text-center text-neutral-500">
          <RotateCcw className="w-6 h-6 animate-spin mx-auto text-blue-500 mb-2" />
          <p className="text-xs">Loading directory...</p>
        </div>
      ) : packages.length === 0 ? (
        <div className="p-16 text-center border border-dashed rounded-2xl text-neutral-400">
          No matching packages found.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {packages.map((pkg) => (
            <PackageCard
              key={pkg.id}
              pkg={pkg}
              onInstallClick={(p) => {
                setSelectedPkg(p);
                setIsInstallOpen(true);
              }}
            />
          ))}
        </div>
      )}

      {selectedPkg && (
        <InstallModal
          pkg={selectedPkg}
          isOpen={isInstallOpen}
          onClose={() => {
            setIsInstallOpen(false);
            setSelectedPkg(null);
          }}
          onInstalled={fetchPackages}
        />
      )}
    </div>
  );
}

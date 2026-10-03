"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Terminal, ArrowLeft } from "lucide-react";
import { marketplaceService } from "@/services/marketplace";
import { SandboxTester } from "@/components/features/marketplace/SandboxTester";

export default function MarketplaceSandboxPage() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await marketplaceService.listPackages({ limit: 50 });
        setPackages(res?.packages || res?.items || []);
      } catch (err) {
        console.error("Failed to load packages for sandbox", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-blue-500" />
            Marketplace Package Sandbox
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Simulate and dry-run workflow packages with sample inputs, synthetic artifacts, and mock tool outputs.
          </p>
        </div>

        <Link
          href="/app/marketplace"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Marketplace
        </Link>
      </div>

      <SandboxTester packages={packages} />
    </div>
  );
}

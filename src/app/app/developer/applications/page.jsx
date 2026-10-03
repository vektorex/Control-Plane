"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppWindow, ChevronLeft, Plus } from "lucide-react";
import { developerService } from "@/services/developer";
import { ApplicationTable } from "@/components/features/developer/ApplicationTable";
import { ApplicationModal } from "@/components/features/developer/ApplicationModal";

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadApps() {
    setLoading(true);
    try {
      const res = await developerService.listApplications();
      setApplications(res.applications || []);
    } catch (err) {
      console.error("Failed to load applications", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApps();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/app/developer"
            className="p-1.5 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <ChevronLeft className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              Developer Applications
            </h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Registered API client applications and environment scopes.
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Application
        </button>
      </div>

      <ApplicationTable
        applications={applications}
        onRefresh={loadApps}
        onOpenCreateModal={() => setIsModalOpen(true)}
      />

      <ApplicationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={loadApps}
      />
    </div>
  );
}

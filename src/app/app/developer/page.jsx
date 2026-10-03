"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Code2, AppWindow, Key, Webhook, Terminal, BookOpen, Activity, ArrowRight, ShieldCheck } from "lucide-react";
import { developerService } from "@/services/developer";
import { DeveloperOverviewCards } from "@/components/features/developer/DeveloperOverviewCards";
import { ApplicationTable } from "@/components/features/developer/ApplicationTable";
import { ApplicationModal } from "@/components/features/developer/ApplicationModal";

export default function DeveloperPlatformDashboard() {
  const [overview, setOverview] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [ovData, appsData] = await Promise.all([
        developerService.getOverview().catch(() => null),
        developerService.listApplications().catch(() => ({ applications: [] })),
      ]);
      setOverview(ovData);
      setApplications(appsData.applications || []);
    } catch (err) {
      console.error("Failed to load developer platform data", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Code2 className="w-6 h-6 text-blue-500" />
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              Developer Platform & Public API
            </h1>
          </div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Programmatic access, scoped credentials, webhooks, rate quotas, and official SDKs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/app/developer/sandbox"
            className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 text-neutral-800 dark:text-neutral-200 transition-colors"
          >
            <Terminal className="w-3.5 h-3.5" />
            Sandbox
          </Link>
          <Link
            href="/app/developer/docs"
            className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700/50 text-neutral-800 dark:text-neutral-200 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5" />
            API Docs
          </Link>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            + New Application
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <DeveloperOverviewCards overview={overview || {}} />

      {/* Quick Nav Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          href="/app/developer/applications"
          className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 hover:border-blue-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <AppWindow className="w-5 h-5 text-blue-500" />
            <ArrowRight className="w-4 h-4 text-neutral-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <div className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
            Applications
          </div>
          <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Manage registered clients and environment targets.
          </div>
        </Link>

        <Link
          href="/app/developer/credentials"
          className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 hover:border-emerald-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <Key className="w-5 h-5 text-emerald-500" />
            <ArrowRight className="w-4 h-4 text-neutral-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <div className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
            Credentials
          </div>
          <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Generate, rotate, and revoke scoped API keys.
          </div>
        </Link>

        <Link
          href="/app/developer/webhooks"
          className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 hover:border-purple-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <Webhook className="w-5 h-5 text-purple-500" />
            <ArrowRight className="w-4 h-4 text-neutral-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <div className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
            Webhooks
          </div>
          <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Configure asynchronous event delivery subscriptions.
          </div>
        </Link>

        <Link
          href="/app/developer/api-explorer"
          className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 hover:border-cyan-500/50 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <Terminal className="w-5 h-5 text-cyan-500" />
            <ArrowRight className="w-4 h-4 text-neutral-400 group-hover:translate-x-1 transition-transform" />
          </div>
          <div className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
            API Explorer
          </div>
          <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
            Interactive request preview and endpoint tester.
          </div>
        </Link>
      </div>

      {/* Applications Directory */}
      <ApplicationTable
        applications={applications}
        onRefresh={loadData}
        onOpenCreateModal={() => setIsModalOpen(true)}
      />

      <ApplicationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={loadData}
      />
    </div>
  );
}

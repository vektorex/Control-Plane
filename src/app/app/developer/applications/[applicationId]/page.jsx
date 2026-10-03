"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppWindow, ChevronLeft, Key, Webhook, Activity, Clock, ShieldCheck, CheckCircle2 } from "lucide-react";
import { developerService } from "@/services/developer";
import { CredentialTable } from "@/components/features/developer/CredentialTable";
import { CredentialModal } from "@/components/features/developer/CredentialModal";
import { WebhookTable, WebhookModal } from "@/components/features/developer/WebhookTable";

export default function ApplicationDetailPage() {
  const params = useParams();
  const applicationId = params?.applicationId;

  const [application, setApplication] = useState(null);
  const [credentials, setCredentials] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [usage, setUsage] = useState(null);
  const [activeTab, setActiveTab] = useState("credentials");
  const [isCredModalOpen, setIsCredModalOpen] = useState(false);
  const [isWebhookModalOpen, setIsWebhookModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadAll() {
    if (!applicationId) return;
    setLoading(true);
    try {
      const [appData, credsData, whData, usageData] = await Promise.all([
        developerService.getApplication(applicationId),
        developerService.listCredentials(applicationId).catch(() => ({ credentials: [] })),
        developerService.listWebhooks(applicationId).catch(() => ({ webhooks: [] })),
        developerService.getApplicationUsage(applicationId).catch(() => null),
      ]);
      setApplication(appData);
      setCredentials(credsData.credentials || []);
      setWebhooks(whData.webhooks || []);
      setUsage(usageData);
    } catch (err) {
      console.error("Failed to load application details", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, [applicationId]);

  if (loading && !application) {
    return (
      <div className="p-8 text-center text-xs text-neutral-500">
        Loading application details...
      </div>
    );
  }

  if (!application) {
    return (
      <div className="p-8 text-center text-xs text-rose-500">
        Application not found.
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Breadcrumb & Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/app/developer/applications"
            className="p-1.5 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <ChevronLeft className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                {application.name}
              </h1>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  application.environment === "production"
                    ? "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
                    : "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                }`}
              >
                {application.environment}
              </span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              {application.description || "No description provided."}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-200 dark:border-neutral-800 pb-2">
        <button
          onClick={() => setActiveTab("credentials")}
          className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "credentials"
              ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold"
              : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200"
          }`}
        >
          <Key className="w-3.5 h-3.5" />
          API Credentials ({credentials.length})
        </button>
        <button
          onClick={() => setActiveTab("webhooks")}
          className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "webhooks"
              ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold"
              : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200"
          }`}
        >
          <Webhook className="w-3.5 h-3.5" />
          Webhooks ({webhooks.length})
        </button>
        <button
          onClick={() => setActiveTab("usage")}
          className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "usage"
              ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold"
              : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Usage & Telemetry
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === "credentials" && (
        <CredentialTable
          credentials={credentials}
          onRefresh={loadAll}
          onOpenCreateModal={() => setIsCredModalOpen(true)}
        />
      )}

      {activeTab === "webhooks" && (
        <WebhookTable
          webhooks={webhooks}
          onRefresh={loadAll}
          onOpenCreateModal={() => setIsWebhookModalOpen(true)}
        />
      )}

      {activeTab === "usage" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="text-xs text-neutral-500 mb-1">Total Invocations (24h)</div>
              <div className="text-2xl font-bold">{usage?.total_requests || 0}</div>
            </div>
            <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="text-xs text-neutral-500 mb-1">Error Rate</div>
              <div className="text-2xl font-bold">{((usage?.error_rate || 0) * 100).toFixed(1)}%</div>
            </div>
            <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="text-xs text-neutral-500 mb-1">Average Latency</div>
              <div className="text-2xl font-bold">{usage?.average_latency_ms || 0}ms</div>
            </div>
            <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
              <div className="text-xs text-neutral-500 mb-1">Task Runs / Workflow Runs</div>
              <div className="text-2xl font-bold">{usage?.task_runs || 0} / {usage?.workflow_runs || 0}</div>
            </div>
          </div>
        </div>
      )}

      <CredentialModal
        isOpen={isCredModalOpen}
        onClose={() => setIsCredModalOpen(false)}
        applicationId={applicationId}
        onCreated={loadAll}
      />

      <WebhookModal
        isOpen={isWebhookModalOpen}
        onClose={() => setIsWebhookModalOpen(false)}
        applicationId={applicationId}
        onCreated={loadAll}
      />
    </div>
  );
}

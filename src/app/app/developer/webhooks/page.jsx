"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Webhook, ChevronLeft, Plus } from "lucide-react";
import { developerService } from "@/services/developer";
import { WebhookTable, WebhookModal } from "@/components/features/developer/WebhookTable";

export default function WebhooksDirectoryPage() {
  const [applications, setApplications] = useState([]);
  const [selectedAppId, setSelectedAppId] = useState("");
  const [webhooks, setWebhooks] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadApps() {
    try {
      const res = await developerService.listApplications();
      const apps = res.applications || [];
      setApplications(apps);
      if (apps.length > 0 && !selectedAppId) {
        setSelectedAppId(apps[0].id);
      }
    } catch (err) {
      console.error("Failed to load applications", err);
    }
  }

  async function loadWebhooks(appId) {
    if (!appId) return;
    setLoading(true);
    try {
      const res = await developerService.listWebhooks(appId);
      setWebhooks(res.webhooks || []);
    } catch (err) {
      console.error("Failed to load webhooks", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApps();
  }, []);

  useEffect(() => {
    if (selectedAppId) {
      loadWebhooks(selectedAppId);
    }
  }, [selectedAppId]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/app/developer"
            className="p-1.5 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <ChevronLeft className="w-4 h-4 text-neutral-600 dark:text-neutral-400" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
              Webhook Subscriptions
            </h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Configure asynchronous HTTP event callbacks with HMAC-SHA256 signature verification.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {applications.length > 0 && (
            <select
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              className="text-xs px-3 py-1.5 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 focus:outline-none"
            >
              {applications.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.environment})
                </option>
              ))}
            </select>
          )}

          {selectedAppId && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              New Webhook
            </button>
          )}
        </div>
      </div>

      <WebhookTable
        webhooks={webhooks}
        onRefresh={() => loadWebhooks(selectedAppId)}
        onOpenCreateModal={() => setIsModalOpen(true)}
      />

      {selectedAppId && (
        <WebhookModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          applicationId={selectedAppId}
          onCreated={() => loadWebhooks(selectedAppId)}
        />
      )}
    </div>
  );
}

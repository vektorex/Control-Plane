"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Key, ChevronLeft, Plus } from "lucide-react";
import { developerService } from "@/services/developer";
import { CredentialTable } from "@/components/features/developer/CredentialTable";
import { CredentialModal } from "@/components/features/developer/CredentialModal";

export default function CredentialsDirectoryPage() {
  const [applications, setApplications] = useState([]);
  const [selectedAppId, setSelectedAppId] = useState("");
  const [credentials, setCredentials] = useState([]);
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

  async function loadCredentials(appId) {
    if (!appId) return;
    setLoading(true);
    try {
      const res = await developerService.listCredentials(appId);
      setCredentials(res.credentials || []);
    } catch (err) {
      console.error("Failed to load credentials", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadApps();
  }, []);

  useEffect(() => {
    if (selectedAppId) {
      loadCredentials(selectedAppId);
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
              API Credentials
            </h1>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Manage scoped API keys, perform zero-downtime rotation, and revoke access.
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
              className="flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Generate Key
            </button>
          )}
        </div>
      </div>

      <CredentialTable
        credentials={credentials}
        onRefresh={() => loadCredentials(selectedAppId)}
        onOpenCreateModal={() => setIsModalOpen(true)}
      />

      {selectedAppId && (
        <CredentialModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          applicationId={selectedAppId}
          onCreated={() => loadCredentials(selectedAppId)}
        />
      )}
    </div>
  );
}

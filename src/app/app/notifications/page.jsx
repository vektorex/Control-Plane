"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Info,
  Archive,
  CheckCheck,
  RefreshCw,
  Filter,
  ExternalLink,
  ChevronRight,
  Shield,
  Layers,
  Settings,
  Send,
  X,
} from "lucide-react";
import { notificationService } from "@/services/notifications";
import { useWorkspace } from "@/lib/workspaceContext";
import { useEventStream } from "@/lib/events";

const severityConfig = {
  info: { icon: Info, color: "text-sky-400 bg-sky-950/40 border-sky-800/40" },
  success: { icon: CheckCircle2, color: "text-emerald-400 bg-emerald-950/40 border-emerald-800/40" },
  warning: { icon: AlertTriangle, color: "text-amber-400 bg-amber-950/40 border-amber-800/40" },
  error: { icon: AlertOctagon, color: "text-rose-400 bg-rose-950/40 border-rose-800/40" },
  critical: { icon: AlertOctagon, color: "text-red-400 bg-red-950/50 border-red-800/60" },
};

export default function NotificationCenterPage() {
  const { activeWorkspace } = useWorkspace();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterUnread, setFilterUnread] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterSource, setFilterSource] = useState("");
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const [list, countRes] = await Promise.all([
        notificationService.listNotifications({
          unread_only: filterUnread,
          severity: filterSeverity || undefined,
          source_type: filterSource || undefined,
          limit: 50,
        }),
        notificationService.getUnreadCount(),
      ]);
      setNotifications(Array.isArray(list) ? list : []);
      if (countRes?.unread_count !== undefined) {
        setUnreadCount(countRes.unread_count);
      }
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  }, [filterUnread, filterSeverity, filterSource]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Step 26: Real-time SSE updates for Notification Center
  const { isConnected: isSseConnected, isPollingFallback } = useEventStream({
    workspaceId: activeWorkspace?.id,
    eventType: "notification.*",
    onEvent: (event) => {
      if (event.type === "notification.created") {
        setUnreadCount((prev) => prev + 1);
        const newNotif = {
          id: event.metadata?.notification_id || event.id,
          title: event.data?.title || event.type,
          body: event.data?.body || "",
          severity: event.data?.severity || "info",
          status: "unread",
          read: false,
          created_at: event.timestamp || new Date().toISOString(),
          source_type: event.aggregate?.type || "system",
          source_id: event.aggregate?.id || "",
          metadata_json: event.data || {},
        };
        setNotifications((prev) => {
          if (prev.some((n) => n.id === newNotif.id)) return prev;
          return [newNotif, ...prev];
        });
      } else {
        fetchNotifications();
      }
    },
    fallbackPollingInterval: 15000,
    fallbackPollingFn: fetchNotifications,
  });

  const handleMarkRead = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await notificationService.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: "read", read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
      if (selectedNotification?.id === id) {
        setSelectedNotification((prev) => ({ ...prev, status: "read", read: true }));
      }
    } catch (err) {
      console.error("Error marking read:", err);
    }
  };

  const handleArchive = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await notificationService.archiveNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      if (selectedNotification?.id === id) {
        setSelectedNotification(null);
      }
    } catch (err) {
      console.error("Error archiving notification:", err);
    }
  };

  const handleMarkAllRead = async () => {
    setActionLoading(true);
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, status: "read", read: true }))
      );
      setUnreadCount(0);
    } catch (err) {
      console.error("Error marking all read:", err);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Bell className="w-6 h-6 text-indigo-400" />
              Notification Center
            </h1>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {unreadCount} unread
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time delivery of completed work, approvals, failures, and system events.
          </p>
        </div>

        {/* Quick Links & Actions */}
        <div className="flex items-center gap-2 self-stretch sm:self-auto flex-wrap">
          <div
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-800"
            title={isSseConnected ? "Real-time execution stream connected" : isPollingFallback ? "Polling fallback active" : "Connecting..."}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isSseConnected ? "bg-emerald-400 animate-pulse" : isPollingFallback ? "bg-amber-400" : "bg-slate-500"
              }`}
            />
            <span className="text-slate-300 text-[10px]">
              {isSseConnected ? "LIVE SSE" : isPollingFallback ? "POLL" : "SYNC"}
            </span>
          </div>
          <Link
            href="/app/notifications/deliveries"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:border-slate-700 hover:text-white transition-colors"
          >
            <Send className="w-3.5 h-3.5 text-slate-400" />
            Delivery Logs
          </Link>
          <Link
            href="/app/settings/notifications"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:border-slate-700 hover:text-white transition-colors"
          >
            <Settings className="w-3.5 h-3.5 text-slate-400" />
            Preferences
          </Link>
          <button
            onClick={handleMarkAllRead}
            disabled={actionLoading || unreadCount === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            Mark All Read
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex flex-wrap items-center gap-2">
          {/* Unread toggle */}
          <button
            onClick={() => setFilterUnread(!filterUnread)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterUnread
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-slate-800/70 text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
          >
            Unread Only
          </button>

          {/* Severity selector */}
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-800/70 text-slate-300 border border-slate-700/60 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Severities</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
            <option value="critical">Critical</option>
          </select>

          {/* Source selector */}
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-800/70 text-slate-300 border border-slate-700/60 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Sources</option>
            <option value="workflow_run">Workflow</option>
            <option value="trigger">Trigger</option>
            <option value="job">Background Job</option>
            <option value="document">Document</option>
            <option value="evaluation_experiment">Evaluation Lab</option>
            <option value="replay_run">Replay</option>
            <option value="connector">Connector</option>
          </select>
        </div>

        <button
          onClick={fetchNotifications}
          disabled={loading}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title="Refresh notifications"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Notifications List */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
          <p className="text-sm">Fetching notifications...</p>
        </div>
      ) : notifications.length === 0 ? (
        <div className="py-20 text-center rounded-2xl bg-slate-900/30 border border-slate-800/60 p-8 space-y-3">
          <div className="w-12 h-12 rounded-full bg-slate-800/50 flex items-center justify-center mx-auto text-slate-500">
            <Bell className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-200">No notifications found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {filterUnread
              ? "You're all caught up! No unread notifications matching current filters."
              : "Completed workflow runs, approvals, and events will appear here."}
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {notifications.map((notif) => {
            const isUnread = notif.status === "unread" || notif.read === false;
            const sevInfo = severityConfig[notif.severity] || severityConfig.info;
            const SevIcon = sevInfo.icon;

            return (
              <div
                key={notif.id}
                onClick={() => setSelectedNotification(notif)}
                className={`relative group p-4 rounded-xl border transition-all cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                  isUnread
                    ? "bg-slate-900/90 border-indigo-500/30 hover:border-indigo-500/50 shadow-sm"
                    : "bg-slate-900/40 border-slate-800/70 hover:border-slate-700/80 text-slate-300"
                }`}
              >
                {/* Left Indicator & Icon */}
                <div className="flex items-start gap-3.5 min-w-0">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center border shrink-0 mt-0.5 ${sevInfo.color}`}
                  >
                    <SevIcon className="w-4 h-4" />
                  </div>

                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {isUnread && (
                        <span className="w-2 h-2 rounded-full bg-indigo-500 shrink-0" title="Unread" />
                      )}
                      <h4
                        className={`text-sm font-semibold truncate ${
                          isUnread ? "text-white" : "text-slate-300"
                        }`}
                      >
                        {notif.title}
                      </h4>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700/60">
                        {notif.event_type}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 line-clamp-2">{notif.body}</p>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-0.5">
                      {notif.source_type && (
                        <span>
                          Source:{" "}
                          <span className="text-slate-300 font-mono">
                            {notif.source_type}
                            {notif.source_id ? ` #${notif.source_id.slice(0, 8)}` : ""}
                          </span>
                        </span>
                      )}
                      <span>
                        {notif.created_at ? new Date(notif.created_at).toLocaleString() : ""}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  {isUnread && (
                    <button
                      onClick={(e) => handleMarkRead(notif.id, e)}
                      className="px-2.5 py-1 rounded-md text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 hover:text-white transition-colors border border-slate-700/60"
                      title="Mark as read"
                    >
                      Mark Read
                    </button>
                  )}
                  <button
                    onClick={(e) => handleArchive(notif.id, e)}
                    className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                    title="Archive notification"
                  >
                    <Archive className="w-4 h-4" />
                  </button>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-200 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Notification Detail Drawer */}
      {selectedNotification && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-slate-950/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-xl h-full max-h-[90vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">Notification Details</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                  {selectedNotification.event_type}
                </span>
              </div>
              <button
                onClick={() => setSelectedNotification(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5 text-sm">
              <div>
                <h3 className="text-lg font-bold text-white mb-2">{selectedNotification.title}</h3>
                <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {selectedNotification.body}
                </p>
              </div>

              {/* Metadata Attributes */}
              <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Severity</span>
                  <span className="font-semibold capitalize text-slate-200">
                    {selectedNotification.severity}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Status</span>
                  <span className="font-semibold capitalize text-slate-200">
                    {selectedNotification.status}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Source Type</span>
                  <span className="font-mono text-slate-300">
                    {selectedNotification.source_type || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Source ID</span>
                  <span className="font-mono text-slate-300 truncate block">
                    {selectedNotification.source_id || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Created At</span>
                  <span className="text-slate-300">
                    {selectedNotification.created_at
                      ? new Date(selectedNotification.created_at).toLocaleString()
                      : "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Read At</span>
                  <span className="text-slate-300">
                    {selectedNotification.read_at
                      ? new Date(selectedNotification.read_at).toLocaleString()
                      : "Unread"}
                  </span>
                </div>
              </div>

              {/* JSON Metadata Payload */}
              {selectedNotification.metadata_json &&
                Object.keys(selectedNotification.metadata_json).length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Payload Metadata
                    </span>
                    <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs font-mono text-slate-300 overflow-x-auto max-h-60">
                      {JSON.stringify(selectedNotification.metadata_json, null, 2)}
                    </pre>
                  </div>
                )}
            </div>

            {/* Drawer Footer Actions */}
            <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-900/80">
              <button
                onClick={() => handleArchive(selectedNotification.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 transition-colors"
              >
                <Archive className="w-4 h-4" />
                Archive
              </button>

              <div className="flex items-center gap-2">
                {(selectedNotification.status === "unread" || !selectedNotification.read) && (
                  <button
                    onClick={() => handleMarkRead(selectedNotification.id)}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-500 transition-colors shadow-sm"
                  >
                    <CheckCheck className="w-4 h-4" />
                    Mark Read
                  </button>
                )}
                <button
                  onClick={() => setSelectedNotification(null)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

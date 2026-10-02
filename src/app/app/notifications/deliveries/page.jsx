"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Send,
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Radio,
  Mail,
  Smartphone,
  ChevronRight,
  ExternalLink,
  Shield,
  Layers,
  X,
} from "lucide-react";
import { notificationService } from "@/services/notifications";

const channelIcons = {
  in_app: { icon: Smartphone, label: "In-App", color: "text-indigo-400 bg-indigo-950/40 border-indigo-800/40" },
  webhook: { icon: Radio, label: "Webhook", color: "text-cyan-400 bg-cyan-950/40 border-cyan-800/40" },
  email: { icon: Mail, label: "Email", color: "text-amber-400 bg-amber-950/40 border-amber-800/40" },
};

const statusBadges = {
  sent: "bg-emerald-950/40 text-emerald-400 border-emerald-800/50",
  sending: "bg-sky-950/40 text-sky-400 border-sky-800/50 animate-pulse",
  queued: "bg-slate-800/60 text-slate-300 border-slate-700/60",
  retrying: "bg-amber-950/40 text-amber-400 border-amber-800/50",
  failed: "bg-rose-950/40 text-rose-400 border-rose-800/50",
  cancelled: "bg-slate-900 text-slate-400 border-slate-800",
};

export default function DeliveriesPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [channelFilter, setChannelFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedDelivery, setSelectedDelivery] = useState(null);

  const fetchDeliveries = useCallback(async () => {
    setLoading(true);
    try {
      const res = await notificationService.listDeliveries({
        channel: channelFilter || undefined,
        status: statusFilter || undefined,
        limit: 50,
      });
      if (res?.deliveries) {
        setDeliveries(res.deliveries);
        setTotal(res.total || res.deliveries.length);
      } else if (Array.isArray(res)) {
        setDeliveries(res);
        setTotal(res.length);
      }
    } catch (err) {
      console.error("Failed to load delivery logs:", err);
    } finally {
      setLoading(false);
    }
  }, [channelFilter, statusFilter]);

  useEffect(() => {
    fetchDeliveries();
  }, [fetchDeliveries]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/app/notifications"
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Notifications
            </Link>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Send className="w-6 h-6 text-indigo-400" />
            Delivery Audit Logs
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Durable background delivery execution history across In-App, Webhooks, and Email channels.
          </p>
        </div>

        {/* Refresh button */}
        <div className="flex items-center gap-2">
          <button
            onClick={fetchDeliveries}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:border-slate-700 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex flex-wrap items-center gap-2">
          {/* Channel selector */}
          <select
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-800/70 text-slate-300 border border-slate-700/60 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Channels</option>
            <option value="in_app">In-App</option>
            <option value="webhook">Webhook</option>
            <option value="email">Email</option>
          </select>

          {/* Status selector */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-800/70 text-slate-300 border border-slate-700/60 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="sent">Sent</option>
            <option value="sending">Sending</option>
            <option value="queued">Queued</option>
            <option value="retrying">Retrying</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Showing {deliveries.length} of {total} records
        </span>
      </div>

      {/* Deliveries Table */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400" />
          <p className="text-sm">Loading delivery records...</p>
        </div>
      ) : deliveries.length === 0 ? (
        <div className="py-20 text-center rounded-2xl bg-slate-900/30 border border-slate-800/60 p-8 space-y-3">
          <Send className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No delivery logs found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Outbound notification transmissions through the Step 24 background queue will be tracked here.
          </p>
        </div>
      ) : (
        <div className="border border-slate-800/80 rounded-xl overflow-hidden bg-slate-950/40">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="p-3.5">Channel</th>
                  <th className="p-3.5">Destination</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Attempts</th>
                  <th className="p-3.5">Scheduled / Sent</th>
                  <th className="p-3.5">Details</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {deliveries.map((deliv) => {
                  const chan = channelIcons[deliv.channel] || channelIcons.in_app;
                  const ChanIcon = chan.icon;
                  const badgeClass = statusBadges[deliv.status] || statusBadges.queued;

                  return (
                    <tr
                      key={deliv.id}
                      onClick={() => setSelectedDelivery(deliv)}
                      className="hover:bg-slate-900/50 transition-colors cursor-pointer group"
                    >
                      {/* Channel */}
                      <td className="p-3.5">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${chan.color}`}
                        >
                          <ChanIcon className="w-3 h-3" />
                          {chan.label}
                        </span>
                      </td>

                      {/* Destination */}
                      <td className="p-3.5 max-w-xs truncate font-mono text-slate-300">
                        {deliv.destination}
                      </td>

                      {/* Status */}
                      <td className="p-3.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeClass}`}
                        >
                          {deliv.status}
                        </span>
                      </td>

                      {/* Attempts */}
                      <td className="p-3.5 font-mono text-slate-400">
                        {deliv.attempt_count} / {deliv.max_attempts}
                      </td>

                      {/* Timestamps */}
                      <td className="p-3.5 text-slate-400 whitespace-nowrap">
                        {deliv.sent_at ? (
                          <span className="text-emerald-400">
                            {new Date(deliv.sent_at).toLocaleTimeString()}
                          </span>
                        ) : (
                          <span>Sched: {new Date(deliv.scheduled_at).toLocaleTimeString()}</span>
                        )}
                      </td>

                      {/* Error or Message ID */}
                      <td className="p-3.5 text-slate-400 max-w-xs truncate">
                        {deliv.error_code ? (
                          <span className="text-rose-400 font-mono">
                            {deliv.error_code}: {deliv.error_message}
                          </span>
                        ) : deliv.provider_message_id ? (
                          <span className="font-mono text-slate-400">
                            ID: {deliv.provider_message_id}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="p-3.5 text-right">
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-200 inline-block transition-transform group-hover:translate-x-0.5" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Delivery Detail Modal */}
      {selectedDelivery && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-white">Delivery Record Details</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                    statusBadges[selectedDelivery.status] || statusBadges.queued
                  }`}
                >
                  {selectedDelivery.status}
                </span>
              </div>
              <button
                onClick={() => setSelectedDelivery(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <div>
                  <span className="text-slate-400 block mb-0.5">Delivery ID</span>
                  <span className="font-mono text-slate-300 truncate block">
                    {selectedDelivery.id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Notification ID</span>
                  <span className="font-mono text-slate-300 truncate block">
                    {selectedDelivery.notification_id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Channel</span>
                  <span className="font-semibold text-slate-200 uppercase font-mono">
                    {selectedDelivery.channel}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Attempt Count</span>
                  <span className="font-mono text-slate-300">
                    {selectedDelivery.attempt_count} / {selectedDelivery.max_attempts}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-400 block mb-0.5">Destination</span>
                  <span className="font-mono text-slate-200 break-all">
                    {selectedDelivery.destination}
                  </span>
                </div>
              </div>

              {selectedDelivery.error_code && (
                <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-800/50 space-y-1">
                  <span className="font-bold text-rose-400 block">
                    Error: {selectedDelivery.error_code}
                  </span>
                  <p className="text-slate-300 whitespace-pre-wrap font-mono text-[11px]">
                    {selectedDelivery.error_message}
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setSelectedDelivery(null)}
                className="px-4 py-1.5 rounded-lg text-xs bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

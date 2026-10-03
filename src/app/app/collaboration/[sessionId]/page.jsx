"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  Users,
  Clock,
  ShieldAlert,
  PowerOff,
  Activity,
  Calendar,
} from "lucide-react";
import { collaborationService } from "@/services/collaboration";
import { CollaborationShell } from "@/components/features/collaboration/CollaborationShell";

export default function CollaborationSessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId;

  const [session, setSession] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sess, acts] = await Promise.all([
        collaborationService.getSession(sessionId),
        collaborationService.listActivity(sessionId, { limit: 20 }),
      ]);
      setSession(sess);
      setActivities(Array.isArray(acts) ? acts : []);
    } catch (err) {
      setError(err.message || "Failed to load collaboration session");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId]);

  const handleCloseSession = async () => {
    if (!confirm("Are you sure you want to close this collaboration session? Real-time streams will terminate; comments, activity, and decisions remain preserved.")) {
      return;
    }
    try {
      await collaborationService.closeSession(sessionId);
      loadSession();
    } catch (err) {
      alert(err.message || "Failed to close session");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-xs text-slate-500 animate-pulse">
        Loading collaboration session...
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
        <ShieldAlert className="w-10 h-10 text-rose-500 mb-3" />
        <h2 className="text-sm font-bold text-slate-200">Unable to access session</h2>
        <p className="text-xs text-slate-500 max-w-sm mt-1 mb-4">{error || "Session not found or access denied."}</p>
        <Link
          href="/app/collaboration"
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium"
        >
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full animate-in fade-in">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          href="/app/collaboration"
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Collaboration Dashboard</span>
        </Link>

        {session.status === "active" && (
          <button
            onClick={handleCloseSession}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/30 border border-slate-800 hover:border-rose-900/50 text-slate-400 hover:text-rose-400 text-xs font-medium transition-colors"
          >
            <PowerOff className="w-3.5 h-3.5" />
            <span>Close Session</span>
          </button>
        )}
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Main Embeddable Collaboration Shell */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <CollaborationShell
            sessionId={session.id}
            resourceType={session.resource_type}
            resourceId={session.resource_id}
            currentUserId={session.created_by}
          />
        </div>

        {/* Right Col: Session Metadata & Audit Activity History */}
        <div className="flex flex-col gap-4">
          {/* Metadata Card */}
          <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col gap-3">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Session Details</h4>

            <div className="space-y-2 text-xs font-mono text-slate-400">
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <span
                  className={`font-semibold capitalize ${
                    session.status === "active" ? "text-emerald-400" : "text-slate-400"
                  }`}
                >
                  {session.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Resource:</span>
                <span className="text-slate-300 font-semibold">{session.resource_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Resource ID:</span>
                <span className="text-slate-300 truncate max-w-[160px]">{session.resource_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Workspace:</span>
                <span className="text-slate-300">{session.workspace_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Created:</span>
                <span>{new Date(session.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}</span>
              </div>
            </div>
          </div>

          {/* Activity Feed */}
          <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Activity History</h4>
            </div>

            <div className="flex flex-col gap-2 max-h-[360px] overflow-y-auto">
              {activities.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs">No activity entries yet.</div>
              ) : (
                activities.map((act) => (
                  <div
                    key={act.id}
                    className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs flex flex-col gap-0.5"
                  >
                    <div className="flex items-center justify-between text-[10px] text-slate-500">
                      <span className="font-semibold text-slate-300 uppercase">{act.activity_type}</span>
                      <span>
                        {new Date(act.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="text-slate-300 leading-snug">{act.summary}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

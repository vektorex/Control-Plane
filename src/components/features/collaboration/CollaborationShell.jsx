"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Users, Activity, MessageSquare, Bookmark, Cpu, AlertCircle, Wifi, WifiOff } from "lucide-react";
import { collaborationService } from "@/services/collaboration";
import { PresenceBar } from "./PresenceBar";
import { CommentThread } from "./CommentThread";
import { CoExecutionPanel } from "./CoExecutionPanel";
import { AssignmentCard } from "./AssignmentCard";
import { AnnotationOverlay } from "./AnnotationOverlay";
import { ConflictResolutionModal } from "./ConflictResolutionModal";

export function CollaborationShell({
  sessionId,
  resourceType,
  resourceId,
  currentUserId = "current-user",
  className = "",
}) {
  const [session, setSession] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [comments, setComments] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [annotations, setAnnotations] = useState([]);
  const [activeRun, setActiveRun] = useState(null);
  const [activeTab, setActiveTab] = useState("discussion"); // discussion, execution, assignments, annotations
  const [conflict, setConflict] = useState(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load session data
  const loadData = useCallback(async () => {
    if (!sessionId) return;
    try {
      const [sess, parts, comms, assigns, anns] = await Promise.allSettled([
        collaborationService.getSession(sessionId),
        collaborationService.listParticipants(sessionId),
        collaborationService.listComments(sessionId),
        collaborationService.listAssignments(sessionId),
        collaborationService.listAnnotations(sessionId),
      ]);

      if (sess.status === "fulfilled") setSession(sess.value);
      if (parts.status === "fulfilled") setParticipants(parts.value || []);
      if (comms.status === "fulfilled") setComments(comms.value || []);
      if (assigns.status === "fulfilled") setAssignments(assigns.value || []);
      if (anns.status === "fulfilled") setAnnotations(anns.value || []);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Presence heartbeat interval (every 30s)
  useEffect(() => {
    if (!sessionId) return;
    const interval = setInterval(() => {
      collaborationService.recordHeartbeat(sessionId, { status: "active" }).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // Real-time SSE subscription
  useEffect(() => {
    if (!sessionId) return;
    setConnected(true);

    const unsubscribe = collaborationService.subscribeEvents(
      sessionId,
      (event) => {
        setConnected(true);
        // Dispatch incoming real-time updates
        if (event.event_type?.startsWith("collaboration.comment")) {
          collaborationService.listComments(sessionId).then(setComments).catch(() => {});
        } else if (event.event_type?.startsWith("collaboration.presence") || event.event_type?.startsWith("collaboration.participant")) {
          collaborationService.listParticipants(sessionId).then(setParticipants).catch(() => {});
        } else if (event.event_type?.startsWith("collaboration.assignment")) {
          collaborationService.listAssignments(sessionId).then(setAssignments).catch(() => {});
        } else if (event.event_type?.startsWith("collaboration.annotation")) {
          collaborationService.listAnnotations(sessionId).then(setAnnotations).catch(() => {});
        } else if (event.event_type?.startsWith("collaboration.run")) {
          if (event.payload?.run_id) {
            setActiveRun((prev) => ({ ...(prev || {}), id: event.payload.run_id, status: event.payload.status || "executing" }));
          }
        }
      },
      () => {
        setConnected(false);
      }
    );

    return () => {
      unsubscribe();
    };
  }, [sessionId]);

  const handleAddComment = async (data) => {
    try {
      const added = await collaborationService.addComment(sessionId, data);
      setComments((prev) => [...prev, added]);
    } catch (err) {
      if (err.status === 409 || err.message?.includes("409")) {
        setConflict({ resource_id: resourceId, current_version: 2, expected_version: 1 });
      }
    }
  };

  const handleResolveComment = async (commentId) => {
    await collaborationService.updateComment(commentId, { status: "resolved" });
    setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, status: "resolved" } : c)));
  };

  const handleDeleteComment = async (commentId) => {
    await collaborationService.deleteComment(commentId);
    setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, status: "deleted", body: "[Deleted]" } : c)));
  };

  const handleCreateAssignment = async (data) => {
    const created = await collaborationService.createAssignment(sessionId, data);
    setAssignments((prev) => [...prev, created]);
  };

  const handleUpdateAssignmentStatus = async (assignmentId, status) => {
    const updated = await collaborationService.updateAssignment(assignmentId, { status });
    setAssignments((prev) => prev.map((a) => (a.id === assignmentId ? updated : a)));
  };

  const handleCreateAnnotation = async (data) => {
    const created = await collaborationService.createAnnotation(sessionId, data);
    setAnnotations((prev) => [...prev, created]);
  };

  const handleInitiateRun = async (data) => {
    const run = await collaborationService.initiateRun(sessionId, data);
    setActiveRun(run);
  };

  const handlePauseRun = async (runId) => {
    const run = await collaborationService.pauseRun(runId);
    setActiveRun(run);
  };

  const handleResumeRun = async (runId) => {
    const run = await collaborationService.resumeRun(runId);
    setActiveRun(run);
  };

  const handleCancelRun = async (runId) => {
    const run = await collaborationService.cancelRun(runId);
    setActiveRun(run);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-xs text-slate-500 animate-pulse">
        Connecting to shared collaboration session...
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-3 rounded-2xl bg-slate-950/90 border border-slate-800 p-4 backdrop-blur-xl shadow-xl ${className}`}>
      {/* Top Header & Connection State */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-indigo-500/20 text-indigo-400">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-200">
              Shared AI Workspace: <span className="text-indigo-400 font-mono">{resourceType}</span>
            </h3>
            <p className="text-[10px] text-slate-500 font-mono">Resource ID: {resourceId || session?.resource_id}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium border ${
              connected
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }`}
          >
            {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            <span>{connected ? "Live Stream Connected" : "Connecting..."}</span>
          </div>
        </div>
      </div>

      {/* Live Presence Bar */}
      <PresenceBar participants={participants} currentUserId={currentUserId} />

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 border-b border-slate-800 pt-1 text-xs">
        {[
          { id: "discussion", label: "Discussion", count: comments.length, icon: MessageSquare },
          { id: "execution", label: "AI Co-Execution", active: Boolean(activeRun), icon: Cpu },
          { id: "assignments", label: "Assignments", count: assignments.length, icon: Users },
          { id: "annotations", label: "Annotations", count: annotations.length, icon: Bookmark },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 font-medium border-b-2 transition-all ${
                isActive
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-300"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-[10px] text-slate-400">
                  {tab.count}
                </span>
              )}
              {tab.active && (
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              )}
            </button>
          );
        })}
      </div>

      {/* Active Tab Views */}
      <div className="pt-1">
        {activeTab === "discussion" && (
          <CommentThread
            comments={comments}
            currentUserId={currentUserId}
            onAddComment={handleAddComment}
            onResolveComment={handleResolveComment}
            onDeleteComment={handleDeleteComment}
          />
        )}

        {activeTab === "execution" && (
          <CoExecutionPanel
            session={session}
            activeRun={activeRun}
            onInitiateRun={handleInitiateRun}
            onPauseRun={handlePauseRun}
            onResumeRun={handleResumeRun}
            onCancelRun={handleCancelRun}
          />
        )}

        {activeTab === "assignments" && (
          <AssignmentCard
            assignments={assignments}
            currentUserId={currentUserId}
            onCreateAssignment={handleCreateAssignment}
            onUpdateStatus={handleUpdateAssignmentStatus}
          />
        )}

        {activeTab === "annotations" && (
          <AnnotationOverlay
            annotations={annotations}
            currentUserId={currentUserId}
            onCreateAnnotation={handleCreateAnnotation}
          />
        )}
      </div>

      {/* Optimistic Concurrency Conflict Modal */}
      {conflict && (
        <ConflictResolutionModal
          conflict={conflict}
          onCancel={() => setConflict(null)}
          onResolve={async (strategy) => {
            setConflict(null);
            await loadData();
          }}
        />
      )}
    </div>
  );
}

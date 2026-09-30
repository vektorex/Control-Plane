"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  ArrowLeft,
  Layers,
  Edit3,
  RefreshCw,
  ExternalLink,
  AlertOctagon,
  FileCode,
  History,
  User,
  Calendar,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { hitlService } from "@/services/hitl";

export default function ApprovalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const requestId = params.requestId;

  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit Mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editedPayloadJson, setEditedPayloadJson] = useState("");

  // Action Dialog state
  const [actionType, setActionType] = useState(null); // "approve", "reject", "cancel", "edit_submit"
  const [actionComment, setActionComment] = useState("");
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState("");

  const fetchRequest = async () => {
    if (!requestId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await hitlService.getRequest(requestId);
      setRequest(data);
      setEditedPayloadJson(JSON.stringify(data.input_snapshot || {}, null, 2));
    } catch (err) {
      console.error("Failed to load approval request:", err);
      setError(err.message || "Failed to load request details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequest();
  }, [requestId]);

  const handleExecuteAction = async () => {
    if (!actionType) return;
    setSubmittingAction(true);
    setActionError("");

    try {
      if (actionType === "approve") {
        await hitlService.approveRequest(requestId, actionComment);
      } else if (actionType === "reject") {
        await hitlService.rejectRequest(requestId, actionComment);
      } else if (actionType === "cancel") {
        await hitlService.cancelRequest(requestId, actionComment);
      } else if (actionType === "edit_submit") {
        let parsed;
        try {
          parsed = JSON.parse(editedPayloadJson);
        } catch (e) {
          setActionError("Invalid JSON syntax in edited payload.");
          setSubmittingAction(false);
          return;
        }
        await hitlService.editRequest(requestId, parsed, actionComment);
      }
      setActionType(null);
      setIsEditing(false);
      await fetchRequest();
    } catch (err) {
      console.error(`Action ${actionType} failed:`, err);
      setActionError(err.message || `Failed to process ${actionType}.`);
    } finally {
      setSubmittingAction(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-24 bg-slate-950 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-500/60 mb-3" />
        <p className="text-sm">Loading intervention request...</p>
      </div>
    );
  }

  if (error || !request) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-24 bg-slate-950 text-slate-300">
        <XCircle className="w-12 h-12 text-red-400 mb-3" />
        <h3 className="text-base font-semibold">Request Not Found</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">{error || "Intervention request does not exist."}</p>
        <Link href="/app/approvals" className="mt-4">
          <Button variant="outline" size="sm" className="gap-1.5 border-slate-700 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Approvals
          </Button>
        </Link>
      </div>
    );
  }

  const isDestructive = request.safe_context?.is_destructive || request.priority === "critical";
  const expiresDate = request.expires_at ? new Date(request.expires_at) : null;
  const isExpired = expiresDate && new Date() > expiresDate;
  const isPending = request.status === "pending" && !isExpired;

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950 text-slate-100 pb-16">
      {/* Top Header */}
      <div className="border-b border-slate-800/80 bg-slate-900/40 px-6 py-5">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <Link
            href="/app/approvals"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Control Center
          </Link>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400">ID: {request.id}</span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto w-full px-6 py-6 space-y-6">
        {/* Title and Badges Bar */}
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800/90 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {request.intervention_type.toUpperCase()}
              </span>
              {isDestructive ? (
                <Badge variant="destructive" className="bg-red-950/80 border-red-500/40 text-red-300">
                  Critical Destructive
                </Badge>
              ) : (
                <Badge className="bg-amber-950/80 border-amber-500/40 text-amber-300">
                  {request.priority.toUpperCase()} PRIORITY
                </Badge>
              )}
              <Badge
                className={
                  request.status === "pending"
                    ? "bg-amber-500/15 text-amber-300 border-amber-500/30 animate-pulse"
                    : request.status === "approved"
                    ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                    : request.status === "edited"
                    ? "bg-indigo-500/15 text-indigo-300 border-indigo-500/30"
                    : "bg-red-500/15 text-red-300 border-red-500/30"
                }
              >
                {request.status.toUpperCase()}
              </Badge>
            </div>

            <span className="text-xs text-slate-400 font-mono">
              Created: {new Date(request.created_at).toLocaleString()}
            </span>
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">{request.title}</h1>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              {request.description || `Authorization requested for operation '${request.requested_action}'.`}
            </p>
          </div>

          {/* Warning Banner for Destructive Actions */}
          {isDestructive && (
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 flex items-start gap-3 text-red-200">
              <AlertOctagon className="w-5 h-5 shrink-0 text-red-400 mt-0.5" />
              <div>
                <p className="font-semibold text-xs text-red-300">Mandatory Human Authorization Required</p>
                <p className="text-[11px] text-red-400 mt-0.5">
                  This operation modifies or deletes resources permanently. AI agents are strictly prohibited from self-authorizing destructive actions.
                </p>
              </div>
            </div>
          )}

          {/* Approval Meaning */}
          {request.safe_context?.approval_meaning && (
            <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/20 text-indigo-200 text-xs flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <span>{request.safe_context.approval_meaning}</span>
            </div>
          )}
        </div>

        {/* Action Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Execution Scope</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Operation</span>
                <span className="font-mono text-slate-200 font-semibold">{request.requested_action}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Target System</span>
                <span className="font-mono text-slate-300">{request.safe_context?.target_system || "Tool / Workflow"}</span>
              </div>
              {request.workflow_run_id && (
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-500">Workflow Run</span>
                  <Link
                    href={`/app/workflows/${request.workflow_id}/runs/${request.workflow_run_id}`}
                    className="font-mono text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    View Run
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              )}
              {request.step_id && (
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Step Identifier</span>
                  <span className="font-mono text-slate-300">{request.step_id}</span>
                </div>
              )}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Review & Governance</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Assigned Reviewer</span>
                <span className="text-slate-300 font-mono">
                  {request.assigned_to ? request.assigned_to : "Any Workspace Admin"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-500">Expires At</span>
                <span className={`font-mono ${isExpired ? "text-red-400 font-semibold" : "text-slate-300"}`}>
                  {expiresDate ? expiresDate.toLocaleString() : "No Expiration"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Current Status</span>
                <span className="font-medium text-slate-300 capitalize">{request.status}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Safe Context & Payload Section */}
        <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                {isEditing ? "Edit Action Payload (Authoritative)" : "Safe Input Snapshot (Credentials Redacted)"}
              </h3>
            </div>

            {isPending && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(!isEditing)}
                className="h-7 text-xs border-indigo-500/40 text-indigo-300 hover:bg-indigo-950/40 gap-1"
              >
                <Edit3 className="w-3 h-3" />
                {isEditing ? "View Original Safe Input" : "Edit Before Executing"}
              </Button>
            )}
          </div>

          {/* High-level preview fields if available */}
          {request.safe_context?.preview_fields && Object.keys(request.safe_context.preview_fields).length > 0 && !isEditing && (
            <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 grid grid-cols-2 gap-3 text-xs">
              {Object.entries(request.safe_context.preview_fields).map(([k, v]) => (
                <div key={k}>
                  <span className="text-slate-500 capitalize">{k.replace("_", " ")}:</span>{" "}
                  <span className="text-slate-200 font-mono font-medium">{String(v)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Payload Display or Editor */}
          {isEditing ? (
            <div className="space-y-2">
              <textarea
                rows={12}
                value={editedPayloadJson}
                onChange={(e) => setEditedPayloadJson(e.target.value)}
                className="w-full p-3 bg-slate-950 border border-slate-700 rounded-lg font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
              <p className="text-[11px] text-indigo-400">
                Modifying this payload replaces the original proposed inputs. The edited parameters will be used when the tool or connector executes.
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-slate-950 p-4 border border-slate-850 overflow-x-auto">
              <pre className="text-xs font-mono text-slate-300 leading-relaxed">
                {JSON.stringify(request.input_snapshot || {}, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Decision History / Audit Trail Timeline */}
        {request.decisions && request.decisions.length > 0 && (
          <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <History className="w-4 h-4 text-slate-500" />
              Decision Audit Log
            </h3>
            <div className="space-y-2.5">
              {request.decisions.map((dec) => (
                <div
                  key={dec.id}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start justify-between text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        className={
                          dec.decision === "approve"
                            ? "bg-emerald-500/20 text-emerald-300"
                            : dec.decision === "edit"
                            ? "bg-indigo-500/20 text-indigo-300"
                            : "bg-red-500/20 text-red-300"
                        }
                      >
                        {dec.decision.toUpperCase()}
                      </Badge>
                      <span className="font-mono text-slate-400">By User: {dec.user_id}</span>
                    </div>
                    {dec.comment && <p className="text-slate-300 italic">"{dec.comment}"</p>}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(dec.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Primary Action Buttons Bar */}
        {isPending && (
          <div className="sticky bottom-4 p-4 rounded-xl bg-slate-900/90 backdrop-blur border border-slate-800 flex items-center justify-between shadow-2xl">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>Execution is paused. Server-side validation will enforce your decision.</span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setActionType("cancel");
                  setActionComment("");
                }}
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                Cancel Request
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setActionType("reject");
                  setActionComment("");
                }}
                className="text-red-400 hover:bg-red-950/40 hover:text-red-300 text-xs"
              >
                Reject Action
              </Button>

              {isEditing ? (
                <Button
                  size="sm"
                  onClick={() => {
                    setActionType("edit_submit");
                    setActionComment("");
                  }}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs"
                >
                  Confirm Edited & Execute
                </Button>
              ) : (
                <Button
                  size="sm"
                  onClick={() => {
                    setActionType("approve");
                    setActionComment("");
                  }}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-md shadow-emerald-950/40"
                >
                  Approve Execution
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {actionType && (
        <Modal
          isOpen={!!actionType}
          onClose={() => setActionType(null)}
          title={
            actionType === "approve"
              ? "Approve Action Execution"
              : actionType === "reject"
              ? "Reject Action Execution"
              : actionType === "cancel"
              ? "Cancel Intervention Request"
              : "Authorize Edited Payload"
          }
        >
          <div className="space-y-4 py-2 text-xs">
            <p className="text-slate-300">
              {actionType === "approve"
                ? "This will resume workflow execution with the original proposed inputs."
                : actionType === "reject"
                ? "This will reject the action and halt the attached workflow run."
                : actionType === "cancel"
                ? "This will cancel the intervention request."
                : "This will resume workflow execution using the modified JSON payload as authoritative input."}
            </p>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Audit Comment (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="Rationale for this decision..."
                value={actionComment}
                onChange={(e) => setActionComment(e.target.value)}
                className="w-full p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-slate-500"
              />
            </div>

            {actionError && (
              <div className="p-2.5 rounded-lg bg-red-950/50 border border-red-500/50 text-red-300 text-xs">
                {actionError}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setActionType(null)}>
                Back
              </Button>
              <Button
                size="sm"
                onClick={handleExecuteAction}
                disabled={submittingAction}
                className={
                  actionType === "reject" || actionType === "cancel"
                    ? "bg-red-600 hover:bg-red-500 text-white"
                    : actionType === "edit_submit"
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                    : "bg-emerald-600 hover:bg-emerald-500 text-white"
                }
              >
                {submittingAction ? "Processing..." : "Confirm Decision"}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

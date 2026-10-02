"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  ExternalLink,
  Edit3,
  RefreshCw,
  Search,
  Filter,
  User,
  Sliders,
  AlertOctagon,
  ArrowRight,
  Shield,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { useWorkspace } from "@/lib/workspaceContext";
import { hitlService } from "@/services/hitl";
import { useEventStream } from "@/lib/events";

export default function ApprovalsPage() {
  const { activeWorkspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState("pending"); // pending, decisions, expired, assigned
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");

  // Decision Modal State
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [actionType, setActionType] = useState(null); // "approve", "reject", "edit"
  const [actionComment, setActionComment] = useState("");
  const [editedPayloadJson, setEditedPayloadJson] = useState("");
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState("");

  // Policy Drawer/Modal State
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [policyData, setPolicyData] = useState(null);
  const [savingPolicy, setSavingPolicy] = useState(false);

  // Load requests
  const fetchRequests = async () => {
    setLoading(true);
    try {
      let statusParam = null;
      if (activeTab === "pending") statusParam = "pending";
      else if (activeTab === "expired") statusParam = "expired";

      const data = await hitlService.listRequests({
        status: statusParam,
        limit: 100,
      });
      setRequests(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load intervention requests:", err);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [activeTab, activeWorkspace]);

  // Step 26: Real-time execution stream for human approvals with polling fallback
  const { isConnected: isSseConnected, isPollingFallback } = useEventStream({
    workspaceId: activeWorkspace?.id,
    eventType: "approval.*",
    onEvent: (event) => {
      fetchRequests();
    },
    fallbackPollingInterval: 10000,
    fallbackPollingFn: fetchRequests,
  });

  // Load Policies
  const fetchPolicies = async () => {
    try {
      const pol = await hitlService.getPolicies();
      setPolicyData(pol);
    } catch (err) {
      console.error("Failed to load approval policies:", err);
    }
  };

  const handleOpenPolicyModal = async () => {
    setShowPolicyModal(true);
    await fetchPolicies();
  };

  const handleSavePolicy = async () => {
    if (!policyData) return;
    setSavingPolicy(true);
    try {
      const updated = await hitlService.updatePolicies({
        require_tool_approval: policyData.require_tool_approval,
        require_connector_write_approval: policyData.require_connector_write_approval,
        require_external_action_approval: policyData.require_external_action_approval,
        require_evaluation_failure_review: policyData.require_evaluation_failure_review,
        max_auto_cost: policyData.max_auto_cost,
      });
      setPolicyData(updated);
      setShowPolicyModal(false);
    } catch (err) {
      console.error("Failed to update policy:", err);
    } finally {
      setSavingPolicy(false);
    }
  };

  // Filter requests according to tab, search query, and priority
  const filteredRequests = useMemo(() => {
    return requests.filter((r) => {
      // Tab filtering
      if (activeTab === "pending" && r.status !== "pending") return false;
      if (activeTab === "decisions" && !["approved", "rejected", "edited", "cancelled"].includes(r.status)) return false;
      if (activeTab === "expired" && r.status !== "expired") return false;
      if (activeTab === "assigned" && !r.assigned_to) return false;

      // Priority filter
      if (priorityFilter !== "all" && r.priority !== priorityFilter) return false;

      // Search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const titleMatch = (r.title || "").toLowerCase().includes(query);
        const actionMatch = (r.requested_action || "").toLowerCase().includes(query);
        const descMatch = (r.description || "").toLowerCase().includes(query);
        return titleMatch || actionMatch || descMatch;
      }
      return true;
    });
  }, [requests, activeTab, priorityFilter, searchQuery]);

  // Stats calculation
  const stats = useMemo(() => {
    const pendingList = requests.filter((r) => r.status === "pending");
    const criticalPending = pendingList.filter((r) => r.priority === "critical" || r.safe_context?.is_destructive);
    const recentApproved = requests.filter((r) => r.status === "approved" || r.status === "edited");
    const expiredList = requests.filter((r) => r.status === "expired");
    return {
      pending: pendingList.length,
      critical: criticalPending.length,
      approved: recentApproved.length,
      expired: expiredList.length,
    };
  }, [requests]);

  // Quick Action Handler
  const handleOpenActionModal = (req, type) => {
    setSelectedRequest(req);
    setActionType(type);
    setActionComment("");
    setActionError("");
    if (type === "edit") {
      setEditedPayloadJson(JSON.stringify(req.input_snapshot || {}, null, 2));
    }
  };

  const handleExecuteDecision = async () => {
    if (!selectedRequest || !actionType) return;
    setSubmittingAction(true);
    setActionError("");
    try {
      if (actionType === "approve") {
        await hitlService.approveRequest(selectedRequest.id, actionComment);
      } else if (actionType === "reject") {
        await hitlService.rejectRequest(selectedRequest.id, actionComment);
      } else if (actionType === "edit") {
        let parsedData;
        try {
          parsedData = JSON.parse(editedPayloadJson);
        } catch (e) {
          setActionError("Invalid JSON syntax in edited payload.");
          setSubmittingAction(false);
          return;
        }
        await hitlService.editRequest(selectedRequest.id, parsedData, actionComment);
      }
      setSelectedRequest(null);
      await fetchRequests();
    } catch (err) {
      console.error(`Failed to execute ${actionType}:`, err);
      setActionError(err.message || `Failed to ${actionType} intervention request.`);
    } finally {
      setSubmittingAction(false);
    }
  };

  const getRiskBadge = (level) => {
    switch (level) {
      case "critical":
        return <Badge variant="destructive" className="bg-red-950/80 border-red-500/40 text-red-300">Critical Risk</Badge>;
      case "high":
        return <Badge className="bg-orange-950/80 border-orange-500/40 text-orange-300">High Risk</Badge>;
      case "medium":
        return <Badge className="bg-amber-950/80 border-amber-500/40 text-amber-300">Medium Risk</Badge>;
      default:
        return <Badge className="bg-slate-800 border-slate-700 text-slate-300">Low Risk</Badge>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "pending":
        return <Badge className="bg-amber-500/15 text-amber-300 border-amber-500/30 animate-pulse">Pending Review</Badge>;
      case "approved":
        return <Badge className="bg-emerald-500/15 text-emerald-300 border-emerald-500/30">Approved</Badge>;
      case "edited":
        return <Badge className="bg-indigo-500/15 text-indigo-300 border-indigo-500/30">Edit & Approved</Badge>;
      case "rejected":
        return <Badge className="bg-red-500/15 text-red-300 border-red-500/30">Rejected</Badge>;
      case "expired":
        return <Badge className="bg-slate-700/50 text-slate-400 border-slate-600">Expired</Badge>;
      case "cancelled":
        return <Badge className="bg-slate-800 text-slate-400 border-slate-700">Cancelled</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Top Banner & Header */}
      <div className="border-b border-slate-800/80 bg-slate-900/30 px-6 py-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-950/40">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                  Human-in-the-Loop Control Center
                </h1>
                <p className="text-xs text-slate-400">
                  Authoritative authorization gate for destructive, write, and external AI actions.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenPolicyModal}
              className="border-slate-700 hover:bg-slate-800 text-slate-200 gap-1.5 text-xs"
            >
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
              Approval Policies
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchRequests}
              disabled={loading}
              className="border-slate-700 hover:bg-slate-800 text-slate-200 gap-1.5 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="max-w-7xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400">Pending Approvals</p>
              <p className="text-xl font-bold text-amber-300 mt-0.5">{stats.pending}</p>
            </div>
            <Clock className="w-5 h-5 text-amber-400/80" />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400">Critical / Destructive</p>
              <p className="text-xl font-bold text-red-400 mt-0.5">{stats.critical}</p>
            </div>
            <AlertOctagon className="w-5 h-5 text-red-400/80" />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400">Recent Decisions</p>
              <p className="text-xl font-bold text-emerald-300 mt-0.5">{stats.approved}</p>
            </div>
            <CheckCircle2 className="w-5 h-5 text-emerald-400/80" />
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-[11px] font-medium text-slate-400">Expired Requests</p>
              <p className="text-xl font-bold text-slate-400 mt-0.5">{stats.expired}</p>
            </div>
            <XCircle className="w-5 h-5 text-slate-500" />
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto w-full px-6 py-6 flex-1 flex flex-col space-y-6">
        {/* Navigation Tabs and Filters */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/60">
          <div className="flex items-center gap-1.5 p-1 bg-slate-900/90 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveTab("pending")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === "pending"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>Pending Approvals</span>
              {stats.pending > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-500/30 text-amber-200">
                  {stats.pending}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("decisions")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === "decisions"
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Recent Decisions
            </button>
            <button
              onClick={() => setActiveTab("expired")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === "expired"
                  ? "bg-slate-800 text-slate-200 border border-slate-700 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Expired Requests
            </button>
            <button
              onClick={() => setActiveTab("assigned")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === "assigned"
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              My Assigned
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative w-48 sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search requests..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500/50"
              />
            </div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-slate-900/80 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
            >
              <option value="all">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        {/* Requests Cards List */}
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-slate-500">
            <RefreshCw className="w-8 h-8 animate-spin text-amber-500/60 mb-3" />
            <p className="text-sm">Loading intervention requests...</p>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-center rounded-xl bg-slate-900/30 border border-slate-800/60 p-8">
            <ShieldCheck className="w-12 h-12 text-slate-600 mb-3" />
            <h3 className="text-base font-semibold text-slate-200">No requests found</h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              {activeTab === "pending"
                ? "No actions currently require human approval in this workspace."
                : "No matching intervention records for this filter view."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredRequests.map((req) => {
              const isDestructive = req.safe_context?.is_destructive || req.priority === "critical";
              const targetSystem = req.safe_context?.target_system || "workflow_step";
              const expiresDate = req.expires_at ? new Date(req.expires_at) : null;
              const isExpired = expiresDate && new Date() > expiresDate;

              return (
                <div
                  key={req.id}
                  className={`rounded-xl border p-5 flex flex-col justify-between transition-all ${
                    isDestructive
                      ? "bg-red-950/15 border-red-900/40 hover:border-red-700/60"
                      : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="space-y-3">
                    {/* Header line with badges */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-1.5">
                        {getRiskBadge(req.safe_context?.risk_level || req.priority)}
                        {getStatusBadge(req.status)}
                        <span className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/60">
                          {targetSystem}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(req.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>

                    {/* Title and Action Description */}
                    <div>
                      <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
                        {req.title}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {req.description || `Operation: ${req.requested_action}`}
                      </p>
                    </div>

                    {/* Metadata Preview */}
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-slate-800/60">
                      <div>
                        <span className="text-slate-500">Action:</span>{" "}
                        <span className="font-mono text-slate-300">{req.requested_action}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Expires:</span>{" "}
                        <span className={`font-mono ${isExpired ? "text-red-400 font-bold" : "text-slate-300"}`}>
                          {expiresDate ? expiresDate.toLocaleTimeString() : "Never"}
                        </span>
                      </div>
                      {req.workflow_run_id && (
                        <div className="col-span-2 flex items-center gap-1 text-slate-400 truncate">
                          <Layers className="w-3 h-3 text-slate-500 shrink-0" />
                          <span className="text-slate-500">Run ID:</span>
                          <span className="font-mono text-xs text-indigo-300 truncate">{req.workflow_run_id}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div className="pt-4 mt-3 border-t border-slate-800/60 flex items-center justify-between gap-2">
                    <Link
                      href={`/app/approvals/${req.id}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
                    >
                      Review Details
                      <ArrowRight className="w-3 h-3" />
                    </Link>

                    {req.status === "pending" && !isExpired && (
                      <div className="flex items-center gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenActionModal(req, "reject")}
                          className="h-7 px-2.5 text-xs text-red-400 hover:bg-red-950/40 hover:text-red-300"
                        >
                          Reject
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleOpenActionModal(req, "edit")}
                          className="h-7 px-2.5 text-xs border-indigo-500/40 text-indigo-300 hover:bg-indigo-950/40"
                        >
                          Edit & Approve
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleOpenActionModal(req, "approve")}
                          className="h-7 px-3 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-sm"
                        >
                          Approve
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Decision Modal (Approve / Reject / Edit & Approve) */}
      {selectedRequest && (
        <Modal
          isOpen={!!selectedRequest}
          onClose={() => setSelectedRequest(null)}
          title={
            actionType === "approve"
              ? "Approve Action Execution"
              : actionType === "reject"
              ? "Reject Action Execution"
              : "Edit Payload & Authorize Execution"
          }
        >
          <div className="space-y-4 py-2 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">{selectedRequest.title}</span>
                {getRiskBadge(selectedRequest.safe_context?.risk_level || selectedRequest.priority)}
              </div>
              <p className="text-slate-400 mt-1">{selectedRequest.description}</p>
            </div>

            {selectedRequest.safe_context?.is_destructive && (
              <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 flex items-start gap-2.5 text-red-300">
                <AlertOctagon className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
                <div>
                  <p className="font-bold">Destructive Operation Authorization</p>
                  <p className="text-[11px] text-red-400 mt-0.5">
                    This action is classified as destructive. Approving authorizes permanent resource modification or deletion.
                  </p>
                </div>
              </div>
            )}

            {actionType === "edit" && (
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Authoritative Action Payload (JSON)
                </label>
                <textarea
                  rows={8}
                  value={editedPayloadJson}
                  onChange={(e) => setEditedPayloadJson(e.target.value)}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-lg font-mono text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  This edited JSON payload will replace the original AI proposal as the authoritative execution input.
                </p>
              </div>
            )}

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Decision Comment (Optional audit note)
              </label>
              <textarea
                rows={2}
                placeholder="Provide a rationale for audit logs..."
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
              <Button variant="ghost" size="sm" onClick={() => setSelectedRequest(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleExecuteDecision}
                disabled={submittingAction}
                className={
                  actionType === "reject"
                    ? "bg-red-600 hover:bg-red-500 text-white"
                    : actionType === "edit"
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                    : "bg-emerald-600 hover:bg-emerald-500 text-white"
                }
              >
                {submittingAction
                  ? "Processing..."
                  : actionType === "reject"
                  ? "Confirm Rejection"
                  : actionType === "edit"
                  ? "Confirm & Execute Edited"
                  : "Confirm Authorization"}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Workspace Approval Policy Settings Modal */}
      {showPolicyModal && policyData && (
        <Modal
          isOpen={showPolicyModal}
          onClose={() => setShowPolicyModal(false)}
          title="Workspace Approval Policies"
        >
          <div className="space-y-4 py-2 text-xs">
            <p className="text-slate-400">
              Configure deterministic rules for when workflows, tools, and external connectors pause for human authorization.
            </p>

            <div className="space-y-3 pt-2">
              {/* Mandatory Destructive Invariant */}
              <div className="p-3 rounded-lg bg-red-950/20 border border-red-900/40 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-red-300">Destructive Actions Approval</p>
                  <p className="text-[11px] text-slate-400">Mandatory rule: Resource deletions always require human authorization.</p>
                </div>
                <Badge className="bg-red-950 text-red-300 border-red-500/40 font-mono">Enforced (Locked)</Badge>
              </div>

              {/* Connector Write Approval */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-200">Connector Write Approval</p>
                  <p className="text-[11px] text-slate-400">Require authorization before modifying external services (GitHub issues, commits, APIs).</p>
                </div>
                <input
                  type="checkbox"
                  checked={policyData.require_connector_write_approval}
                  onChange={(e) => setPolicyData({ ...policyData, require_connector_write_approval: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600"
                />
              </div>

              {/* Tool Execution Approval */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-200">Tool Execution Approval</p>
                  <p className="text-[11px] text-slate-400">Require human review before internal tools execute state-modifying actions.</p>
                </div>
                <input
                  type="checkbox"
                  checked={policyData.require_tool_approval}
                  onChange={(e) => setPolicyData({ ...policyData, require_tool_approval: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600"
                />
              </div>

              {/* Evaluation Failure Review */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-200">Evaluation Failure Review</p>
                  <p className="text-[11px] text-slate-400">Pause for human review whenever an evaluation step detects issues or failures.</p>
                </div>
                <input
                  type="checkbox"
                  checked={policyData.require_evaluation_failure_review}
                  onChange={(e) => setPolicyData({ ...policyData, require_evaluation_failure_review: e.target.checked })}
                  className="w-4 h-4 accent-indigo-600"
                />
              </div>

              {/* Max Auto Cost */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <label className="block font-semibold text-slate-200 mb-1">
                  Auto-Approval Cost Threshold (USD)
                </label>
                <input
                  type="number"
                  step="0.10"
                  value={policyData.max_auto_cost || ""}
                  placeholder="e.g. 1.00 (Leave empty for no limit)"
                  onChange={(e) => setPolicyData({ ...policyData, max_auto_cost: e.target.value ? parseFloat(e.target.value) : null })}
                  className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none"
                />
                <p className="text-[10px] text-slate-500 mt-1">Actions with an estimated generation cost exceeding this amount trigger human review.</p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setShowPolicyModal(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSavePolicy}
                disabled={savingPolicy}
                className="bg-indigo-600 hover:bg-indigo-500 text-white"
              >
                {savingPolicy ? "Saving..." : "Save Policies"}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

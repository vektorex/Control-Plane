"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  Plus,
  Search,
  Filter,
  Trash2,
  Archive,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Lightbulb,
  Clock,
  Sparkles,
  ShieldCheck,
  Edit2,
  ChevronRight,
  GitCompare,
  Layers,
  FileText,
  User,
  Building,
  Briefcase,
  AlertOctagon,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useWorkspace } from "@/lib/workspaceContext";
import { memoryService } from "@/services/memory";

const MEMORY_TYPES = [
  { value: "all", label: "All Types" },
  { value: "preference", label: "User Preference" },
  { value: "technical_fact", label: "Technical Fact" },
  { value: "instruction", label: "Instruction" },
  { value: "project_context", label: "Project Context" },
  { value: "workflow_context", label: "Workflow Context" },
  { value: "reference", label: "Reference" },
  { value: "decision", label: "Architecture Decision" },
];

export default function MemoryCenterPage() {
  const { activeWorkspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState("my"); // "my", "project", "workspace", "suggestions", "conflicts"
  const [memories, setMemories] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("active");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Create / Edit modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState(null);
  const [modalForm, setModalForm] = useState({
    title: "",
    content: "",
    type: "preference",
    scope: "user",
    importance: "medium",
    expiration: "never",
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  // Load memories, suggestions, and conflicts
  const fetchData = async () => {
    if (!activeWorkspace?.id) return;
    try {
      setIsLoading(true);
      setError(null);

      // Determine scope filter based on tab
      let scopeParam = null;
      if (activeTab === "my") scopeParam = "user";
      if (activeTab === "project") scopeParam = "project";
      if (activeTab === "workspace") scopeParam = "workspace";

      const [mems, suggs, confs] = await Promise.all([
        memoryService.listMemories({
          scope: scopeParam,
          type: typeFilter !== "all" ? typeFilter : undefined,
          status: statusFilter,
          search: searchQuery || undefined,
        }),
        memoryService.listSuggestions("candidate"),
        memoryService.listConflicts("unresolved"),
      ]);

      setMemories(mems || []);
      setSuggestions(suggs || []);
      setConflicts(confs || []);
    } catch (err) {
      console.error("[MemoryCenter] Error loading data:", err);
      setError(err.message || "Failed to load memory data");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeWorkspace?.id, activeTab, typeFilter, statusFilter]);

  const handleOpenCreateModal = () => {
    let defaultScope = "user";
    if (activeTab === "project") defaultScope = "project";
    if (activeTab === "workspace") defaultScope = "workspace";

    setEditingMemory(null);
    setModalForm({
      title: "",
      content: "",
      type: "preference",
      scope: defaultScope,
      importance: "medium",
      expiration: "never",
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (mem) => {
    setEditingMemory(mem);
    setModalForm({
      title: mem.title,
      content: mem.content,
      type: mem.type,
      scope: mem.scope,
      importance: mem.importance,
      expiration: "never",
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSaveMemory = async (e) => {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError(null);

    try {
      if (editingMemory) {
        await memoryService.updateMemory(editingMemory.id, {
          title: modalForm.title,
          content: modalForm.content,
          type: modalForm.type,
          importance: modalForm.importance,
        });
        setActionSuccess("Memory updated successfully.");
      } else {
        await memoryService.createMemory({
          title: modalForm.title,
          content: modalForm.content,
          type: modalForm.type,
          scope: modalForm.scope,
          importance: modalForm.importance,
          expiration: modalForm.expiration,
        });
        setActionSuccess("Memory created successfully.");
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err) {
      setFormError(err.message || "Failed to save memory");
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleArchive = async (memId) => {
    try {
      await memoryService.archiveMemory(memId);
      setActionSuccess("Memory archived.");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRestore = async (memId) => {
    try {
      await memoryService.restoreMemory(memId);
      setActionSuccess("Memory restored to active status.");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (memId) => {
    if (!window.confirm("Are you sure you want to permanently delete this memory?")) return;
    try {
      await memoryService.deleteMemory(memId);
      setActionSuccess("Memory permanently deleted.");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAcceptSuggestion = async (suggId) => {
    try {
      await memoryService.acceptSuggestion(suggId);
      setActionSuccess("Suggestion saved as persistent memory!");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRejectSuggestion = async (suggId) => {
    try {
      await memoryService.rejectSuggestion(suggId);
      setActionSuccess("Suggestion dismissed.");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleResolveConflict = async (conflictId, winnerId) => {
    try {
      await memoryService.resolveConflict(conflictId, {
        action: "keep_winner",
        winner_memory_id: winnerId,
      });
      setActionSuccess("Conflict resolved successfully.");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDismissConflict = async (conflictId) => {
    try {
      await memoryService.resolveConflict(conflictId, {
        action: "dismiss",
      });
      setActionSuccess("Conflict dismissed.");
      fetchData();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-inner">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
                Persistent Memory Center
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Retain user preferences, technical facts, and architectural decisions across tasks with strict scope isolation.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            disabled={isLoading}
            className="border-slate-800 hover:bg-slate-850 text-slate-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={handleOpenCreateModal}
            className="bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-900/30"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            New Memory
          </Button>
        </div>
      </div>

      {/* Security & Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Memories</span>
            <Brain className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{memories.length}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Scoped to {activeTab} view</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">AI Suggestions</span>
            <Lightbulb className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{suggestions.length}</p>
          <span className="text-[11px] text-amber-400/80 mt-1 block">Requires user confirmation</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Unresolved Conflicts</span>
            <GitCompare className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{conflicts.length}</p>
          <span className="text-[11px] text-rose-400/80 mt-1 block">Opposing directives flagged</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-emerald-500/20 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Security & Secret Guard</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-sm font-semibold text-emerald-300 mt-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Enforced & Active
          </p>
          <span className="text-[11px] text-slate-500 mt-1 block">Credentials & PII auto-rejected</span>
        </div>
      </div>

      {/* Action Alerts */}
      {actionSuccess && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-emerald-200">
            &times;
          </button>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200">
            &times;
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("my")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "my"
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <User className="w-3.5 h-3.5" />
            My Memories
          </button>
          <button
            onClick={() => setActiveTab("project")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "project"
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            Project Memories
          </button>
          <button
            onClick={() => setActiveTab("workspace")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "workspace"
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Building className="w-3.5 h-3.5" />
            Workspace Memories
          </button>
          <button
            onClick={() => setActiveTab("suggestions")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "suggestions"
                ? "border-amber-500 text-amber-400 bg-amber-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Lightbulb className="w-3.5 h-3.5" />
            Suggestions
            {suggestions.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-500/20 text-amber-300 font-bold">
                {suggestions.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("conflicts")}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === "conflicts"
                ? "border-rose-500 text-rose-400 bg-rose-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            Conflicts
            {conflicts.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-500/20 text-rose-300 font-bold">
                {conflicts.length}
              </span>
            )}
          </button>
        </div>

        {/* Filter bar for memory views */}
        {activeTab !== "suggestions" && activeTab !== "conflicts" && (
          <div className="flex items-center gap-2 pb-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchData()}
                className="pl-8 pr-3 py-1 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44 sm:w-56"
              />
            </div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="py-1 px-2.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              {MEMORY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="py-1 px-2.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        )}
      </div>

      {/* Main Tab Content */}
      {isLoading ? (
        <div className="py-24 text-center">
          <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-400">Loading persistent context intelligence...</p>
        </div>
      ) : activeTab === "suggestions" ? (
        /* ================= SUGGESTIONS VIEW ================= */
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200 flex items-start gap-3">
            <Lightbulb className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-300">Candidate Memory Suggestions</p>
              <p className="text-amber-200/80 mt-1">
                Candidate memories are detected from task patterns or recurring instructions. They are{" "}
                <strong>never automatically saved</strong> into your persistent context without explicit user confirmation.
              </p>
            </div>
          </div>

          {suggestions.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl">
              <Sparkles className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">No pending suggestions</p>
              <p className="text-xs text-slate-500 mt-1">
                As you run tasks, recurring preferences and decisions will be suggested here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {suggestions.map((sugg) => (
                <div
                  key={sugg.id}
                  className="p-5 rounded-xl bg-slate-900/70 border border-amber-500/30 hover:border-amber-500/50 transition-all flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1">
                        <Sparkles className="w-3 h-3" /> Possible Memory
                      </span>
                      <Badge variant="outline" className="text-[10px] border-slate-800 text-slate-400">
                        {sugg.source_type}
                      </Badge>
                    </div>

                    <h3 className="text-sm font-bold text-slate-100">{sugg.title}</h3>
                    <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                      {sugg.content}
                    </p>

                    <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-[11px] text-indigo-300">
                      <span className="font-semibold text-indigo-200">Why save: </span>
                      {sugg.reason || "Detected recurring pattern that may assist future tasks."}
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800/80">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRejectSuggestion(sugg.id)}
                      className="text-xs border-slate-800 hover:bg-slate-800 text-slate-400"
                    >
                      Dismiss
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleAcceptSuggestion(sugg.id)}
                      className="text-xs bg-amber-600 hover:bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-950/40"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                      Save as Memory
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : activeTab === "conflicts" ? (
        /* ================= CONFLICTS VIEW ================= */
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 text-xs text-rose-200 flex items-start gap-3">
            <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-300">Directly Conflicting Directives</p>
              <p className="text-rose-200/80 mt-1">
                The platform detected contradictory memories in the same scope (e.g., conflicting technology or formatting
                preferences). Resolve the conflict by choosing which directive takes precedence.
              </p>
            </div>
          </div>

          {conflicts.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl">
              <CheckCircle2 className="w-8 h-8 text-emerald-500/60 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">No active memory conflicts</p>
              <p className="text-xs text-slate-500 mt-1">
                All persistent preferences in this workspace are mutually consistent.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {conflicts.map((conf) => (
                <div
                  key={conf.id}
                  className="p-5 rounded-xl bg-slate-900/70 border border-rose-500/30 shadow-sm space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                      <GitCompare className="w-4 h-4" /> Conflict Detected
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(conf.detected_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Memory A */}
                    <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">Existing Memory A</span>
                        <Badge variant="outline" className="text-[10px] border-slate-800">
                          {conf.memory_a?.type || "preference"}
                        </Badge>
                      </div>
                      <p className="text-xs font-semibold text-indigo-300">{conf.memory_a?.title}</p>
                      <p className="text-xs text-slate-400 bg-slate-900 p-2.5 rounded border border-slate-850">
                        {conf.memory_a?.content}
                      </p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleResolveConflict(conf.id, conf.memory_a_id)}
                        className="w-full text-xs border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/10 mt-2"
                      >
                        Keep Memory A (Archive B)
                      </Button>
                    </div>

                    {/* Memory B */}
                    <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">Newer Memory B</span>
                        <Badge variant="outline" className="text-[10px] border-slate-800">
                          {conf.memory_b?.type || "preference"}
                        </Badge>
                      </div>
                      <p className="text-xs font-semibold text-indigo-300">{conf.memory_b?.title}</p>
                      <p className="text-xs text-slate-400 bg-slate-900 p-2.5 rounded border border-slate-850">
                        {conf.memory_b?.content}
                      </p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleResolveConflict(conf.id, conf.memory_b_id)}
                        className="w-full text-xs border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/10 mt-2"
                      >
                        Keep Memory B (Archive A)
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                    <span className="text-[11px] text-slate-500">{conf.resolution}</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDismissConflict(conf.id)}
                      className="text-xs text-slate-400 hover:text-slate-200"
                    >
                      Dismiss (Keep Both Active)
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* ================= STANDARD MEMORIES LIST ================= */
        <div className="space-y-4">
          {memories.length === 0 ? (
            <div className="py-20 text-center border border-dashed border-slate-800 rounded-xl space-y-3">
              <Brain className="w-10 h-10 text-slate-600 mx-auto" />
              <p className="text-sm font-semibold text-slate-300">No memories found</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No persistent memories in this scope match your filter criteria. Create explicit knowledge or approve
                task suggestions.
              </p>
              <Button
                size="sm"
                onClick={handleOpenCreateModal}
                className="mt-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Add First Memory
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {memories.map((mem) => (
                <div
                  key={mem.id}
                  className={`p-5 rounded-xl bg-slate-900/60 border ${
                    mem.status === "archived" ? "border-slate-850 opacity-60" : "border-slate-800/80 hover:border-slate-700"
                  } transition-all flex flex-col justify-between space-y-4 shadow-sm`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <Badge
                        variant="outline"
                        className={`text-[10px] capitalize font-medium ${
                          mem.importance === "high"
                            ? "border-rose-500/40 text-rose-300 bg-rose-500/10"
                            : mem.importance === "medium"
                            ? "border-amber-500/40 text-amber-300 bg-amber-500/10"
                            : "border-slate-800 text-slate-400"
                        }`}
                      >
                        {mem.importance} importance
                      </Badge>
                      <span className="text-[10px] text-slate-500 capitalize flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3" />
                        {mem.last_used_at ? `Used ${new Date(mem.last_used_at).toLocaleDateString()}` : "Never used"}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-sm font-bold text-slate-100 tracking-tight">{mem.title}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-indigo-300 capitalize">
                          {mem.type.replace("_", " ")}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500">
                          {mem.scope} • source: {mem.source_type}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed line-clamp-4 bg-slate-950/40 p-3 rounded-lg border border-slate-850">
                      {mem.content}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 text-xs">
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenEditModal(mem)}
                        className="h-7 px-2 text-slate-400 hover:text-slate-200"
                        title="Edit Memory"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </Button>
                      {mem.status === "archived" ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRestore(mem.id)}
                          className="h-7 px-2 text-emerald-400 hover:text-emerald-300"
                          title="Restore Memory"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleArchive(mem.id)}
                          className="h-7 px-2 text-slate-400 hover:text-amber-400"
                          title="Archive Memory"
                        >
                          <Archive className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(mem.id)}
                      className="h-7 px-2 text-slate-500 hover:text-rose-400"
                      title="Delete Memory"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingMemory ? "Edit Memory" : "Create Explicit Memory"}
      >
        <form onSubmit={handleSaveMemory} className="space-y-4">
          {formError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Memory Title</label>
            <Input
              required
              placeholder="e.g. Preferred programming language"
              value={modalForm.title}
              onChange={(e) => setModalForm({ ...modalForm, title: e.target.value })}
              className="text-xs bg-slate-900 border-slate-800 text-slate-100"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Type</label>
              <select
                value={modalForm.type}
                onChange={(e) => setModalForm({ ...modalForm, type: e.target.value })}
                className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                {MEMORY_TYPES.filter((t) => t.value !== "all").map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Scope</label>
              <select
                disabled={!!editingMemory}
                value={modalForm.scope}
                onChange={(e) => setModalForm({ ...modalForm, scope: e.target.value })}
                className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              >
                <option value="user">User (Private to you)</option>
                <option value="project">Project (Inside current project)</option>
                <option value="workspace">Workspace (All workspace members)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Importance</label>
              <select
                value={modalForm.importance}
                onChange={(e) => setModalForm({ ...modalForm, importance: e.target.value })}
                className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            {!editingMemory && (
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Expiration</label>
                <select
                  value={modalForm.expiration}
                  onChange={(e) => setModalForm({ ...modalForm, expiration: e.target.value })}
                  className="w-full py-2 px-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="never">Never</option>
                  <option value="7_days">7 Days</option>
                  <option value="30_days">30 Days</option>
                  <option value="90_days">90 Days</option>
                </select>
              </div>
            )}
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Content</label>
            <textarea
              required
              rows={4}
              placeholder="e.g. Use JavaScript instead of TypeScript when possible."
              value={modalForm.content}
              onChange={(e) => setModalForm({ ...modalForm, content: e.target.value })}
              className="w-full p-3 text-xs bg-slate-900 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              Do not include API keys, passwords, or credentials. Raw secrets will be rejected.
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsModalOpen(false)}
              className="text-xs border-slate-800 text-slate-400"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={formSubmitting}
              className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              {formSubmitting ? "Saving..." : editingMemory ? "Update Memory" : "Create Memory"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

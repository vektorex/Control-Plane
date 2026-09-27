"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Plus, AlertCircle, Loader2 } from "lucide-react";
import { projectService } from "@/services/projects";

export function CreateTaskModal({ isOpen, onClose, projects = [], onTaskCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [contextText, setContextText] = useState("");
  const [projectId, setProjectId] = useState(projects[0]?.id || "");
  const [status, setStatus] = useState("draft");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  React.useEffect(() => {
    if (projects.length > 0 && !projectId) {
      setProjectId(projects[0].id);
    }
  }, [projects, projectId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please enter a task title");
      return;
    }
    const targetProjId = projectId || projects[0]?.id;
    if (!targetProjId) {
      setError("No project selected. Please create a project first.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError("");
      const payload = {
        title: title.trim(),
        description: description.trim() || undefined,
        instructions: instructions.trim() || undefined,
        context_text: contextText.trim() || undefined,
        status: status,
      };
      const created = await projectService.createProjectTask(targetProjId, payload);
      setTitle("");
      setDescription("");
      setInstructions("");
      setContextText("");
      setStatus("draft");
      onTaskCreated?.(created);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create task");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Work Task"
      description="Define a new AI work task unit with executable instructions and context."
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || (!projectId && projects.length === 0)}
            icon={isSubmitting ? Loader2 : Plus}
          >
            {isSubmitting ? "Creating..." : "Create Task"}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <Input
          label="Task Title / Goal"
          placeholder="e.g. Analyze authentication implementation"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          autoFocus
        />

        <Textarea
          label="AI Instructions"
          placeholder="Detailed instructions for the AI model to execute..."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={3}
        />

        <Textarea
          label="Context / Supplementary Data (Optional)"
          placeholder="Paste relevant code, background text, or data..."
          value={contextText}
          onChange={(e) => setContextText(e.target.value)}
          rows={2}
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Select
            label="Target Project"
            value={projectId || projects[0]?.id || ""}
            onChange={(e) => setProjectId(e.target.value)}
            options={
              projects.length > 0
                ? projects.map((p) => ({ value: p.id, label: p.name }))
                : [{ value: "", label: "No projects available" }]
            }
          />

          <Select
            label="Initial Status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            options={[
              { value: "draft", label: "Draft" },
              { value: "active", label: "Active" },
              { value: "completed", label: "Completed" },
              { value: "archived", label: "Archived" },
            ]}
          />
        </div>
      </form>
    </Modal>
  );
}

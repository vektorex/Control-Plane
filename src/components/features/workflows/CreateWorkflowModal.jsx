"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { workflowService } from "@/services/workflows";
import { useRouter } from "next/navigation";
import { GitBranch, Sparkles } from "lucide-react";

export function CreateWorkflowModal({ isOpen, onClose, onCreated, projects = [] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const payload = {
        name: name.trim(),
        description: description.trim() || undefined,
        project_id: projectId || undefined,
        steps: [
          {
            id: "input_step",
            name: "Workflow Input",
            type: "input",
            config: {},
            enabled: true,
          },
          {
            id: "generate_step",
            name: "AI Generation",
            type: "generate",
            config: {
              prompt_template: "Perform task for: {{input.topic}}",
              temperature: 0.7,
            },
            enabled: true,
          },
          {
            id: "output_step",
            name: "Final Output",
            type: "output",
            config: {
              output_template: "{{steps.generate_step.output}}",
            },
            enabled: true,
          },
        ],
        input_schema: {
          topic: {
            type: "string",
            required: true,
            description: "Primary topic or objective for the workflow",
          },
        },
      };

      const created = await workflowService.createWorkflow(payload);
      if (onCreated) onCreated(created);
      onClose();
      router.push(`/app/workflows/${created.id}`);
    } catch (err) {
      console.error("[CreateWorkflowModal] Failed to create workflow:", err);
      setError(err.message || "Failed to create workflow");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create AI Workflow"
      description="Create a multi-step orchestrated workflow pipeline"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Workflow Name <span className="text-rose-400">*</span>
          </label>
          <Input
            placeholder="e.g. Executive Research & Synthesis"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Description
          </label>
          <textarea
            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none h-20"
            placeholder="Briefly describe what this workflow accomplishes..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {projects.length > 0 && (
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Associated Project (Optional)
            </label>
            <select
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            >
              <option value="">No Project (Workspace Default)</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-850">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting || !name.trim()}>
            {isSubmitting ? "Creating..." : "Create Workflow"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { FolderPlus, AlertCircle, Loader2 } from "lucide-react";
import { workspaceService } from "@/services/workspaces";

export function CreateProjectModal({ isOpen, onClose, workspaceId, onProjectCreated }) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter a project name");
      return;
    }
    if (!workspaceId) {
      setError("Active workspace not selected");
      return;
    }

    try {
      setIsSubmitting(true);
      setError("");
      const payload = {
        name: name.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
      };
      const created = await workspaceService.createWorkspaceProject(workspaceId, payload);
      setName("");
      setSlug("");
      setDescription("");
      onProjectCreated?.(created);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Project Scope"
      description="Initialize a dedicated workspace container for specialized LLM tasks and context."
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting || !name.trim()}
            icon={isSubmitting ? Loader2 : FolderPlus}
          >
            {isSubmitting ? "Creating..." : "Create Project"}
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
          label="Project Name"
          placeholder="e.g. Legal Compliance Document Extraction"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
        />

        <Input
          label="Custom Slug (Optional)"
          placeholder="e.g. legal-compliance-extraction"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
        />

        <Textarea
          label="Scope & Context Description"
          placeholder="Describe the domain, context boundaries, and purpose of this project..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
      </form>
    </Modal>
  );
}

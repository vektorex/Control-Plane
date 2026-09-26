"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { FolderPlus, AlertCircle } from "lucide-react";

export function CreateProjectModal({ isOpen, onClose, onSubmitProject }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter a project name");
      return;
    }

    setIsSubmitting(true);
    setError("");

    const newProject = {
      id: `proj-${Math.floor(100 + Math.random() * 900)}`,
      name: name.trim(),
      description: description.trim(),
      taskCount: 0,
      contextSourcesCount: 0,
      createdAt: new Date().toISOString(),
    };

    onSubmitProject?.(newProject);
    setName("");
    setDescription("");
    setIsSubmitting(false);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Project Scope"
      description="Initialize a dedicated workspace container for specialized LLM tasks, context sets, and tools."
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            isLoading={isSubmitting}
            icon={FolderPlus}
          >
            Create Project
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

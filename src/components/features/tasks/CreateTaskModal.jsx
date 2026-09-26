"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Cpu, Sparkles, Sliders, AlertCircle } from "lucide-react";

export function CreateTaskModal({ isOpen, onClose, onSubmitTask, projects = [] }) {
  const [formData, setFormData] = useState({
    title: "",
    prompt: "",
    projectId: projects[0]?.id || "proj-1",
    executionMode: "auto",
    priority: "medium",
    retrievalStrategy: "hybrid_rag",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      setError("Please enter a task title");
      return;
    }
    if (!formData.prompt.trim()) {
      setError("Please enter task prompt or specification");
      return;
    }

    setIsSubmitting(true);
    setError("");

    // Package payload
    const newTask = {
      id: `task-${Math.floor(100 + Math.random() * 900)}`,
      title: formData.title.trim(),
      prompt: formData.prompt.trim(),
      projectId: formData.projectId,
      projectName: projects.find((p) => p.id === formData.projectId)?.name || "Default Workspace",
      modelAssigned: formData.executionMode === "deep_reasoning" ? "Claude 3.5 Sonnet / o1" : "Auto-Routing",
      priority: formData.priority,
      status: "PENDING",
      retrievalStrategy: formData.retrievalStrategy,
      createdAt: new Date().toISOString(),
    };

    onSubmitTask?.(newTask);
    setIsSubmitting(false);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Dispatch Work Task"
      description="Submit a new goal for orchestrator intent analysis, model selection, and tool execution."
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
            icon={Sparkles}
          >
            Dispatch to Orchestrator
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
          label="Task Title / Goal Summary"
          placeholder="e.g. Audit microservices API contract changes"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          required
        />

        <Textarea
          label="Task Specification & Instructions"
          placeholder="Provide the complete prompt, goal description, inputs, and expected output format..."
          value={formData.prompt}
          onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
          rows={4}
          required
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Select
            label="Project Scope"
            value={formData.projectId}
            onChange={(e) => setFormData({ ...formData, projectId: e.target.value })}
            options={projects.map((p) => ({ value: p.id, label: p.name }))}
          />

          <Select
            label="Priority Level"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            options={[
              { value: "low", label: "Low Priority" },
              { value: "medium", label: "Medium Priority" },
              { value: "high", label: "High Priority" },
              { value: "critical", label: "Critical Priority" },
            ]}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Select
            label="Execution Routing Mode"
            value={formData.executionMode}
            onChange={(e) => setFormData({ ...formData, executionMode: e.target.value })}
            options={[
              { value: "auto", label: "Auto Orchestration (Recommended)" },
              { value: "fast", label: "Low Latency / High Speed" },
              { value: "deep_reasoning", label: "Deep Reasoning Tier" },
              { value: "cost_optimized", label: "Cost Optimized" },
            ]}
          />

          <Select
            label="Retrieval Strategy"
            value={formData.retrievalStrategy}
            onChange={(e) => setFormData({ ...formData, retrievalStrategy: e.target.value })}
            options={[
              { value: "hybrid_rag", label: "Hybrid RAG (Dense + BM25)" },
              { value: "hierarchical_graph", label: "Knowledge Graph Hierarchy" },
              { value: "direct_context", label: "Direct Context Window" },
            ]}
          />
        </div>
      </form>
    </Modal>
  );
}

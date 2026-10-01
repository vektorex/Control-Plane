export const siteConfig = {
  name: "AI Work Layer",
  tagline: "One workspace for getting real work done with LLMs.",
  description:
    "A universal LLM work orchestration platform that accepts complex tasks and intelligently coordinates models, context sources, retrieval strategies, and specialized tools.",
  url: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  version: "0.1.0-alpha",
  mainNav: [
    { label: "Overview", href: "/#overview" },
    { label: "Architecture", href: "/#architecture" },
    { label: "Capabilities", href: "/#capabilities" },
    { label: "Docs", href: "/#docs" },
  ],
  appNav: [
    {
      label: "Dashboard",
      href: "/app",
      icon: "LayoutDashboard",
      description: "System overview, active workloads, and orchestration status",
    },
    {
      label: "Tasks",
      href: "/app/tasks",
      icon: "ListTodo",
      description: "Manage, dispatch, and monitor orchestrated task executions",
    },
    {
      label: "Workflows",
      href: "/app/workflows",
      icon: "Workflow",
      description: "Build, validate, publish, and execute multi-step AI orchestration pipelines",
    },
    {
      label: "Replays",
      href: "/app/replays",
      icon: "RotateCcw",
      description: "Execution replay, trace inspection, diff comparisons, and safe debugging",
    },
    {
      label: "Approvals",
      href: "/app/approvals",
      icon: "ShieldCheck",
      description: "Human-in-the-Loop review, authorization, edit-before-execute, and policies",
    },
    {
      label: "Connectors",
      href: "/app/connectors",
      icon: "Plug",
      description: "Secure external integrations with GitHub, APIs, and data sources",
    },
    {
      label: "Memory",
      href: "/app/memory",
      icon: "Brain",
      description: "Persistent knowledge, user preferences, suggestions, and conflicts",
    },
    {
      label: "Projects",
      href: "/app/projects",
      icon: "FolderKanban",
      description: "Organize work streams, knowledge contexts, and toolsets",
    },
    {
      label: "Documents",
      href: "/app/documents",
      icon: "Files",
      description: "Manage uploaded knowledge base, chunking, and vector index",
    },
    {
      label: "Analytics",
      href: "/app/analytics",
      icon: "BarChart3",
      description: "Observability, token usage, cost tracking, and execution metrics",
    },
    {
      label: "AI Runtime",
      href: "/app/ai-runtime",
      icon: "Cpu",
      description: "Unified AI Gateway status, providers, model health, routing, and usage",
    },
    {
      label: "Playground",
      href: "/app/playground",
      icon: "Terminal",
      description: "Internal developer testbed for LLM abstraction & streaming",
    },
    {
      label: "Settings",
      href: "/app/settings",
      icon: "Settings",
      description: "Configure orchestrator engines, API keys, and system defaults",
    },
  ],
  links: {
    github: "https://github.com/rayulumukku/LLM-Work-Orchestration-Layer",
    docs: "/app/settings",
  },
};

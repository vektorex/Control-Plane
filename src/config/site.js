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

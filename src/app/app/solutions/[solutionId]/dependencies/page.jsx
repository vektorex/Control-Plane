"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function SolutionDependencies({ params }) {
  // params.solutionId
  const [exported, setExported] = useState(false);

  const handleExport = () => {
    const manifest = {
      solution_id: params?.solutionId || "sol-demo-1",
      name: "Automated GitHub Security Review",
      version: "2.1.0",
      dependencies: [
        {
          id: "agent-team-sast",
          type: "agent_team",
          name: "Static Code Analysis Team",
          children: [
            { id: "agent-sast-reviewer", type: "agent", name: "SAST Reviewer v1.2" },
            { id: "model-gpt4", type: "model", name: "GPT-4" },
            { id: "tool-sonarqube", type: "tool", name: "SonarQube Scanner" },
            { id: "agent-dep-auditor", type: "agent", name: "Dependency Auditor v1.0" }
          ]
        },
        {
          id: "connector-github",
          type: "connector",
          name: "GitHub Repository Extractor"
        }
      ],
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `solution-${params?.solutionId || "manifest"}-dependencies.json`;
    a.click();
    URL.revokeObjectURL(url);
    setExported(true);
    setTimeout(() => setExported(false), 3000);
  };
  
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/solutions" className="text-gray-500 hover:text-gray-700">
          Solutions
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/solutions/${params.solutionId}`} className="text-gray-500 hover:text-gray-700">
          Automated GitHub Security Review
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Dependencies</span>
      </nav>

      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold">Dependency Tree</h1>
          <p className="text-gray-500 mt-2">Trace capabilities back to their foundational resources.</p>
        </div>
        <button 
          onClick={handleExport}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 cursor-pointer"
        >
          {exported ? "✓ Manifest Exported" : "Export Dependency Manifest"}
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="space-y-6 relative before:absolute before:inset-0 before:ml-4 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent hidden md:block"></div>
        
        {/* Mock Tree */}
        <div className="space-y-4 text-sm relative">
          
          <div className="flex items-start gap-4">
            <div className="mt-1 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">S</div>
            <div className="flex-1 border border-gray-200 rounded-lg p-4 bg-gray-50">
              <h3 className="font-bold text-gray-900 mb-1">Automated GitHub Security Review (v2.1.0)</h3>
              <p className="text-gray-500 text-xs">Solution Composition</p>
            </div>
          </div>

          <div className="ml-8 pl-4 border-l-2 border-gray-200 space-y-4">
            
            <div className="flex items-start gap-4">
              <div className="mt-1 w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center font-bold text-xs">C</div>
              <div className="flex-1 border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-gray-900">Static Code Analysis Team</h4>
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">Catalog: Agent Team</span>
                </div>
                <div className="ml-4 pl-4 border-l border-dashed border-gray-300 space-y-3 mt-3">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-400">↳</span>
                    <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-600 border border-gray-200">Agent: SAST Reviewer v1.2</span>
                  </div>
                  <div className="ml-8 flex flex-col gap-1 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">↳</span>
                      <span className="text-gray-600">Model: GPT-4 (Authorized)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">↳</span>
                      <span className="text-gray-600">Tool: SonarQube Scanner (Authorized)</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-gray-400">↳</span>
                    <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-600 border border-gray-200">Agent: Dependency Auditor v1.0</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="mt-1 w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold text-xs">C</div>
              <div className="flex-1 border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <h4 className="font-bold text-gray-900">GitHub Repository Extractor</h4>
                  <span className="text-xs bg-orange-100 text-orange-800 px-2 py-0.5 rounded">Catalog: Connector</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

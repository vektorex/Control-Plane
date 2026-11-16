"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function IntentAnalysis({ params }) {
  const resolvedParams = React.use ? React.use(params) : params;
  const requestId = resolvedParams?.requestId || "request";
  const [repoUrl, setRepoUrl] = useState("");
  const [clarificationSubmitted, setClarificationSubmitted] = useState(false);

  const handleSubmitAnswer = () => {
    if (repoUrl.trim()) {
      setClarificationSubmitted(true);
    }
  };
  
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/intent" className="text-gray-500 hover:text-gray-700">
          Intent Workspace
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Request #{requestId}</span>
      </nav>

      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="px-2.5 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">Analysis Complete</span>
        </div>
        <h1 className="text-2xl font-bold mb-4">"Review this GitHub repository for security vulnerabilities and create a verified report"</h1>
        
        {/* Pipeline Progress */}
        <div className="flex items-center gap-2 mt-6">
          <div className="h-2 flex-1 bg-blue-500 rounded-full"></div>
          <div className="h-2 flex-1 bg-blue-500 rounded-full"></div>
          <div className="h-2 flex-1 bg-gray-200 rounded-full"></div>
          <div className="h-2 flex-1 bg-gray-200 rounded-full"></div>
          <div className="h-2 flex-1 bg-gray-200 rounded-full"></div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-2 font-medium">
          <span className="text-blue-600">Intent Analysis</span>
          <span className="text-blue-600">Requirements Check</span>
          <span>Capability Discovery</span>
          <span>Candidate Synthesis</span>
          <span>Review</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4">Extracted Intent Profile</h3>
          <ul className="space-y-4 text-sm">
            <li>
              <span className="block text-gray-500 text-xs uppercase tracking-wider mb-1">Objective</span>
              <span className="font-medium text-gray-900">Security Analysis & Reporting</span>
            </li>
            <li>
              <span className="block text-gray-500 text-xs uppercase tracking-wider mb-1">Inputs Identified</span>
              <span className="font-medium text-gray-900">GitHub Repository URL</span>
            </li>
            <li>
              <span className="block text-gray-500 text-xs uppercase tracking-wider mb-1">Outputs Expected</span>
              <span className="font-medium text-gray-900">Verified Security Report</span>
            </li>
          </ul>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4">Clarification Required</h3>
          {clarificationSubmitted ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 text-green-800 text-sm">
              <span className="font-semibold">✓ Clarification Received:</span> {repoUrl}
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-amber-900 text-sm mb-2">Which repository should be analyzed?</h4>
              <p className="text-xs text-amber-700 mb-3">You mentioned "this GitHub repository" but did not specify a URL.</p>
              <input 
                type="text" 
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="w-full p-2 border border-amber-300 rounded text-sm mb-3 bg-white" 
                placeholder="https://github.com/org/repo" 
              />
              <button 
                onClick={handleSubmitAnswer}
                disabled={!repoUrl.trim()}
                className="px-4 py-2 bg-amber-600 disabled:opacity-50 text-white rounded-lg text-sm font-medium hover:bg-amber-700 cursor-pointer"
              >
                Submit Answer
              </button>
            </div>
          )}
          <p className="text-xs text-gray-500 text-center">Synthesis will pause until mandatory ambiguities are resolved.</p>
        </div>
      </div>

      <div className="flex justify-end gap-3 border-t border-gray-200 pt-6">
        <Link href={`/app/intent/${params.requestId}/requirements`}>
          <button className="px-6 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800">
            View Extracted Requirements →
          </button>
        </Link>
      </div>

    </div>
  );
}

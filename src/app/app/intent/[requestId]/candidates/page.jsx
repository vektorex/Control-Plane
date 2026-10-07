"use client";

import React from 'react';
import Link from 'next/link';

export default function CandidateSolutions({ params }) {
  // params.requestId
  
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/intent" className="text-gray-500 hover:text-gray-700">
          Intent Workspace
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/intent/${params.requestId}`} className="text-gray-500 hover:text-gray-700">
          Request #{params.requestId}
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Candidates</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Candidate Solutions</h1>
        <p className="text-gray-500 mt-2">The system has synthesized 2 potential solutions that fulfill your requirements using available governed capabilities.</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        
        {/* Candidate A */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md hover:border-blue-400 transition-all flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-4">
              <span className="px-2.5 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded-full border border-green-200">
                Recommended Match
              </span>
            </div>
            <h3 className="text-xl font-bold mb-2">Multi-Agent Security Review</h3>
            <p className="text-sm text-gray-600 mb-6 line-clamp-3">
              Uses the specialized "Static Code Analysis Team" from the catalog. This provides deep analysis via specialized agent roles but incurs higher latency and cost.
            </p>
            
            <div className="space-y-3 mb-6">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Composition (4 Components)</h4>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded border border-gray-200">GitHub Connector</span>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded border border-purple-200">Analysis Agent Team</span>
                <span className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded border border-amber-200">Security Lead Approval</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded border border-blue-200">Report Workflow</span>
              </div>
            </div>
          </div>
          
          <div className="pt-4 border-t border-gray-100">
            <Link href={`/app/intent/${params.requestId}/review?candidate=A`}>
              <button className="w-full py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800">
                Review Candidate A
              </button>
            </Link>
          </div>
        </div>

        {/* Candidate B */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md hover:border-blue-400 transition-all flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-4">
              <span className="px-2.5 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded-full border border-gray-200">
                Alternative
              </span>
            </div>
            <h3 className="text-xl font-bold mb-2">Workflow-Driven Analysis</h3>
            <p className="text-sm text-gray-600 mb-6 line-clamp-3">
              Uses a deterministic pipeline workflow. Faster and highly reproducible, but relies on a single generic reasoning pass rather than debate.
            </p>
            
            <div className="space-y-3 mb-6">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Composition (3 Components)</h4>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded border border-gray-200">GitHub Connector</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded border border-blue-200">Pipeline Workflow</span>
                <span className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded border border-amber-200">Security Lead Approval</span>
              </div>
            </div>
          </div>
          
          <div className="pt-4 border-t border-gray-100">
            <Link href={`/app/intent/${params.requestId}/review?candidate=B`}>
              <button className="w-full py-2 border border-gray-300 text-black rounded-lg text-sm font-medium hover:bg-gray-50">
                Review Candidate B
              </button>
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}

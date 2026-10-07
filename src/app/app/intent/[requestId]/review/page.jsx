"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function CandidateReview({ params }) {
  // params.requestId
  const [status, setStatus] = useState('review_required'); // review_required, converting, converted

  const handleConvert = () => {
    setStatus('converting');
    setTimeout(() => {
      setStatus('converted');
    }, 1500);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/intent" className="text-gray-500 hover:text-gray-700">
          Intent Workspace
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/intent/${params.requestId}/candidates`} className="text-gray-500 hover:text-gray-700">
          Candidates
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Review Candidate A</span>
      </nav>

      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Multi-Agent Security Review</h1>
          <p className="text-gray-500">Review the synthesized solution blueprint and execution constraints.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 bg-white text-black">
            Reject & Regenerate
          </button>
          <button 
            onClick={handleConvert}
            disabled={status !== 'review_required'}
            className="px-6 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
          >
            {status === 'review_required' ? 'Accept & Create Solution Draft' : 
             status === 'converting' ? 'Converting...' : 'Converted Successfully ✓'}
          </button>
        </div>
      </div>

      {status === 'converted' && (
        <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
            </div>
            <div>
              <h4 className="font-bold text-green-900">Solution Draft Created</h4>
              <p className="text-sm text-green-800">The candidate has been converted to a STEP 49 Solution Draft. It is not yet published.</p>
            </div>
          </div>
          <Link href="/app/solutions/sol-draft-1">
            <button className="px-4 py-2 bg-white text-green-700 border border-green-300 rounded-lg text-sm font-medium hover:bg-green-50">
              Open Solution Draft →
            </button>
          </Link>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="col-span-2 space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Architecture Topology</h3>
            
            <div className="flex items-center gap-2 mb-6">
              <span className="text-xs bg-gray-100 px-2 py-1 rounded font-medium border border-gray-200">Input: Repo URL</span>
              <span className="text-gray-400">→</span>
              <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded font-medium border border-orange-200">GitHub Connector</span>
              <span className="text-gray-400">→</span>
              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded font-medium border border-purple-200">Analysis Agent Team</span>
              <span className="text-gray-400">→</span>
              <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded font-medium border border-amber-200">Human Approval</span>
              <span className="text-gray-400">→</span>
              <span className="text-xs bg-gray-100 px-2 py-1 rounded font-medium border border-gray-200">Output: Report</span>
            </div>

            <div className="space-y-4">
              <h4 className="text-sm font-bold text-gray-900">Selection Evidence</h4>
              <div className="text-sm text-gray-600 bg-gray-50 border border-gray-100 p-4 rounded-lg space-y-2">
                <p><strong>GitHub Connector:</strong> Selected to satisfy the "repository" input requirement. Catalog item #cat-gh-123 is the only authorized connector for Confidential data.</p>
                <p><strong>Analysis Agent Team:</strong> Selected over simple pipelines to satisfy the implicit complexity of "vulnerabilities" which requires reasoning and debate (Catalog item #cat-team-sec).</p>
                <p><strong>Human Approval:</strong> Injected automatically by Workspace Policy: "External API calls require Data Steward Approval".</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Simulation Results</h3>
            <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-100 rounded-lg mb-4">
              <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <div>
                <h4 className="text-sm font-semibold text-blue-900">Side-Effect Free Verification</h4>
                <p className="text-xs text-blue-800 mt-1">Simulated execution path verifies all inputs map successfully to required outputs. Governance policies resolve cleanly.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Governance Snapshot</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Security Clearance</span>
                <span className="font-medium text-green-600 flex items-center gap-1">Passed <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg></span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Data Classification</span>
                <span className="font-medium text-gray-900">Confidential</span>
              </li>
              <li className="flex justify-between py-1">
                <span className="text-gray-500">Approval Policy</span>
                <span className="font-medium text-amber-600">Strict (Required)</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Dependencies</h3>
            <ul className="space-y-2 text-sm">
              <li className="text-gray-700 flex items-center justify-between">
                <span>Agent Capabilities</span>
                <span className="font-medium">2</span>
              </li>
              <li className="text-gray-700 flex items-center justify-between">
                <span>Connectors</span>
                <span className="font-medium">1</span>
              </li>
              <li className="text-gray-700 flex items-center justify-between">
                <span>Data Mappings</span>
                <span className="font-medium">4</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

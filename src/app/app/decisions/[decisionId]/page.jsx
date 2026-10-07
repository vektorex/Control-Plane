"use client";

import React from 'react';
import Link from 'next/link';

export default function DecisionDetail({ params }) {
  // params.decisionId
  
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/decisions" className="text-gray-500 hover:text-gray-700">
          Decision Intelligence
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">{params.decisionId}</span>
      </nav>

      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="px-2.5 py-0.5 bg-red-100 text-red-800 text-xs font-medium rounded-full flex w-fit items-center gap-1 border border-red-200">
              <div className="w-1.5 h-1.5 rounded-full bg-red-600"></div> Blocked
            </span>
            <span className="text-sm text-gray-500 font-medium">Execution Readiness Assessment</span>
          </div>
          <h1 className="text-3xl font-bold">Customer Contract Analyzer</h1>
          <p className="text-gray-500 mt-2">Subject: Solution #sol-doc-intel</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border border-gray-300 bg-white rounded-lg text-sm font-medium hover:bg-gray-50 text-gray-700">
            View Source Subject
          </button>
          <button className="px-4 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
            Re-evaluate
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        
        {/* Left Col - Overview & Explanation */}
        <div className="col-span-2 space-y-6">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <h2 className="text-red-900 font-bold mb-2 flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              Execution is Blocked
            </h2>
            <p className="text-red-800 text-sm mb-4">
              This solution cannot be executed because a critical dependency is unhealthy and a mandatory governance approval is missing.
            </p>
            
            <div className="bg-white rounded-lg border border-red-100 overflow-hidden">
              <div className="p-4 border-b border-gray-100 flex justify-between items-center">
                <span className="font-semibold text-gray-900 text-sm">Critical Blockers (2)</span>
                <Link href={`/app/decisions/${params.decisionId}/blockers`} className="text-xs text-blue-600 hover:underline">View All</Link>
              </div>
              <ul className="divide-y divide-gray-100 text-sm">
                <li className="p-4 flex items-start gap-3">
                  <div className="mt-0.5 text-red-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  </div>
                  <div>
                    <span className="font-medium text-gray-900 block">Unhealthy Dependency</span>
                    <span className="text-gray-500 block">Connector "PDF Extractor API" is currently degraded (503 errors).</span>
                  </div>
                </li>
                <li className="p-4 flex items-start gap-3">
                  <div className="mt-0.5 text-red-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                  </div>
                  <div>
                    <span className="font-medium text-gray-900 block">Missing Data Governance Approval</span>
                    <span className="text-gray-500 block">Execution on Confidential data requires Data Steward sign-off.</span>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-900">Recommended Actions</h3>
            </div>
            <ul className="space-y-3">
              <li className="flex justify-between items-center p-3 border border-gray-100 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-800">Request Data Steward Approval</span>
                <button className="px-3 py-1.5 bg-black text-white rounded text-xs font-medium hover:bg-gray-800">Request Approval</button>
              </li>
              <li className="flex justify-between items-center p-3 border border-gray-100 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-800">Wait for Connector Recovery</span>
                <span className="text-xs text-gray-500 italic">No manual action available</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right Col - Readiness State */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-900">Readiness Factors</h3>
              <Link href={`/app/decisions/${params.decisionId}/readiness`} className="text-xs text-blue-600 hover:underline">Details</Link>
            </div>
            
            <ul className="space-y-4 text-sm">
              <li className="flex justify-between items-center">
                <span className="text-gray-600">Validation State</span>
                <span className="text-green-600 font-medium flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-500"></div> Passed</span>
              </li>
              <li className="flex justify-between items-center">
                <span className="text-gray-600">Security Policies</span>
                <span className="text-green-600 font-medium flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-500"></div> Clear</span>
              </li>
              <li className="flex justify-between items-center">
                <span className="text-gray-600">Governance Approvals</span>
                <span className="text-red-600 font-medium flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-red-500"></div> Missing</span>
              </li>
              <li className="flex justify-between items-center">
                <span className="text-gray-600">Dependency Health</span>
                <span className="text-red-600 font-medium flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-red-500"></div> Degraded</span>
              </li>
              <li className="flex justify-between items-center pt-3 border-t border-gray-100">
                <span className="text-gray-600">Evidence Freshness</span>
                <span className="text-green-600 font-medium">Fresh (2 mins ago)</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-900">Evidence Provenance</h3>
              <Link href={`/app/decisions/${params.decisionId}/evidence`} className="text-xs text-blue-600 hover:underline">View All</Link>
            </div>
            <p className="text-xs text-gray-500 mb-4">This decision is backed by 8 pieces of deterministic evidence.</p>
            <div className="text-xs space-y-2">
              <div className="p-2 bg-gray-50 rounded border border-gray-100">
                <span className="font-semibold block text-gray-700">Governance Policy #gov-confidential</span>
                <span className="text-gray-500 truncate block mt-1">Rule: Strict approval required for extraction on Confidential data.</span>
              </div>
              <div className="p-2 bg-gray-50 rounded border border-gray-100">
                <span className="font-semibold block text-gray-700">Reliability Monitor #mon-pdf-ext</span>
                <span className="text-gray-500 truncate block mt-1">Status: 503 Service Unavailable (12:04 UTC)</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

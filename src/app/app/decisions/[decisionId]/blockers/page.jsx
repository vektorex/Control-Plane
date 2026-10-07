"use client";

import React from 'react';
import Link from 'next/link';

export default function BlockersView({ params }) {
  // params.decisionId
  
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/decisions" className="text-gray-500 hover:text-gray-700">
          Decision Intelligence
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/decisions/${params.decisionId}`} className="text-gray-500 hover:text-gray-700">
          {params.decisionId}
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Blockers</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-red-900">Execution Blockers</h1>
        <p className="text-gray-500 mt-2">These issues must be resolved before the decision state can become READY.</p>
      </div>

      <div className="space-y-4">
        <div className="bg-white border border-red-200 rounded-xl p-5 shadow-sm flex items-start gap-4">
          <div className="mt-1 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-bold text-gray-900">Missing Data Governance Approval</h3>
              <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded uppercase font-bold tracking-wider">Critical</span>
            </div>
            <p className="text-sm text-gray-600 mb-3">Execution on Confidential data requires Data Steward sign-off.</p>
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">Domain: Data Governance</span>
              <button className="px-3 py-1 bg-black text-white rounded text-xs font-medium hover:bg-gray-800">Remediate: Request Approval</button>
            </div>
          </div>
        </div>

        <div className="bg-white border border-red-200 rounded-xl p-5 shadow-sm flex items-start gap-4">
          <div className="mt-1 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-start mb-1">
              <h3 className="font-bold text-gray-900">Unhealthy Dependency</h3>
              <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded uppercase font-bold tracking-wider">High</span>
            </div>
            <p className="text-sm text-gray-600 mb-3">Connector "PDF Extractor API" is currently degraded (503 errors).</p>
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">Domain: Reliability</span>
              <span className="text-xs text-gray-400 italic">No manual remediation available</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

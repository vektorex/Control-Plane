"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function KnowledgeConflicts() {
  const [resolved, setResolved] = useState(false);
  const [resolutionText, setResolutionText] = useState('');

  const handleResolve = (action) => {
    setResolved(true);
    if (action === 'keep_a') {
      setResolutionText('Resolved: Item A preserved. Candidate Item B rejected.');
    } else {
      setResolutionText('Resolved: Item B accepted as authoritative. Item A deprecated.');
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/knowledge" className="text-gray-500 hover:text-gray-700">
          Organizational Knowledge
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Conflicts</span>
      </nav>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Conflicts</h1>
          <p className="text-gray-500 mt-2">Resolve contradictions in institutional memory.</p>
        </div>
      </div>

      {resolved ? (
        <div className="p-8 text-center bg-white border border-gray-200 rounded-xl">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 mb-3">
            ✓
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Conflict Resolved</h3>
          <p className="text-sm text-gray-600">{resolutionText}</p>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="bg-white border border-red-200 rounded-xl overflow-hidden">
            <div className="bg-red-50 p-4 border-b border-red-200">
              <h3 className="font-semibold text-red-800 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                Direct Contradiction Detected
              </h3>
            </div>
            
            <div className="p-6 grid grid-cols-2 gap-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 mb-2">
                  Item A (Stale)
                </span>
                <h4 className="font-medium mb-2">Frontend Framework Choice</h4>
                <p className="text-sm text-gray-600">"All new frontend applications must be built using React with Create React App."</p>
                <p className="text-xs text-gray-400 mt-4">Verified: Jan 2024</p>
              </div>
              
              <div className="p-4 border border-gray-200 rounded-lg bg-yellow-50">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mb-2">
                  Item B (Candidate)
                </span>
                <h4 className="font-medium mb-2">Frontend Framework Modernization</h4>
                <p className="text-sm text-gray-600">"Create React App is deprecated. New projects must use Next.js App Router."</p>
                <p className="text-xs text-gray-400 mt-4">Extracted: 2 days ago</p>
              </div>
            </div>
            
            <div className="bg-gray-50 px-6 py-4 flex justify-between items-center border-t border-gray-200">
              <span className="text-sm text-gray-500">Conflict prevents Item B from being verified automatically.</span>
              <div className="flex gap-3">
                <button 
                  type="button"
                  onClick={() => handleResolve('keep_a')}
                  className="px-4 py-2 border border-gray-200 bg-white text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium cursor-pointer"
                >
                  Keep A, Reject B
                </button>
                <button 
                  type="button"
                  onClick={() => handleResolve('accept_b')}
                  className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium cursor-pointer"
                >
                  Accept B, Deprecate A
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function SolutionSimulation({ params }) {
  const [status, setStatus] = useState('idle');

  const runSimulation = () => {
    setStatus('running');
    setTimeout(() => {
      setStatus('completed');
    }, 2000);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/solutions" className="text-gray-500 hover:text-gray-700">
          Solutions
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/solutions/${params.solutionId}`} className="text-gray-500 hover:text-gray-700">
          Automated GitHub Security Review
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Simulation</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Simulate Solution Execution</h1>
        <p className="text-gray-500 mt-2">Run a dry-run simulation to identify governance blocks, missing capabilities, or execution bottlenecks before instantiating in production.</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <h3 className="font-semibold text-gray-900 mb-4">Simulation Context</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Target Workspace</label>
              <select className="w-full p-2 border border-gray-300 rounded text-sm bg-white">
                <option>Security Operations (Current)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Acting Identity</label>
              <select className="w-full p-2 border border-gray-300 rounded text-sm bg-white">
                <option>System Default (Service Account)</option>
                <option>My User Identity</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button 
              onClick={runSimulation}
              disabled={status === 'running'}
              className="px-6 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
            >
              {status === 'running' ? 'Simulating...' : 'Run Simulation'}
            </button>
          </div>
        </div>

        {status === 'completed' && (
          <div className="p-6 bg-white">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              </div>
              <div>
                <h3 className="font-bold text-lg text-gray-900">Simulation Successful</h3>
                <p className="text-sm text-gray-500">The execution path is valid and all requirements are resolvable.</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-sm mb-2 text-gray-900">Estimated Path & Governance Profile</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex justify-between items-center text-gray-600">
                    <span>Component Resolution</span>
                    <span className="text-green-600 font-medium">4/4 Resolved</span>
                  </li>
                  <li className="flex justify-between items-center text-gray-600">
                    <span>RBAC Checks</span>
                    <span className="text-green-600 font-medium">Passed</span>
                  </li>
                  <li className="flex justify-between items-center text-gray-600">
                    <span>Data Governance Constraints</span>
                    <span className="text-gray-900">Confidential Enclave Required</span>
                  </li>
                  <li className="flex justify-between items-center text-gray-600 border-t border-gray-100 pt-2 mt-2">
                    <span>Identified Human Checkpoints (HITL)</span>
                    <span className="text-amber-600 font-medium">1 Required (Security Lead Sign-off)</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

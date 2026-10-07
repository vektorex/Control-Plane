"use client";

import React from 'react';
import Link from 'next/link';

export default function ContractBreaches() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/contracts" className="text-gray-500 hover:text-gray-700">
          Contracts
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Breaches</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Contract Breaches</h1>
        <p className="text-gray-500 mt-2">Immutable history of all detected SLA violations and missing acceptance criteria.</p>
      </div>

      <div className="space-y-4">
        {[1, 2].map((breach) => (
          <div key={breach} className="bg-white border border-red-200 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Open Breach
                    </span>
                    <span className="text-sm font-medium text-gray-500">Severity: Major</span>
                  </div>
                  <h3 className="text-lg font-semibold">Cost Limit Exceeded</h3>
                  <Link href={`/app/contracts/ctr-${breach}`}>
                    <span className="text-sm text-blue-600 hover:underline">Contract #CTR-881{breach}</span>
                  </Link>
                </div>
                <span className="text-sm text-gray-500">Detected Oct 11, 2026</span>
              </div>
              
              <div className="bg-red-50 p-4 rounded-lg mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-red-800 mb-1">Expected Limit</div>
                    <div className="font-mono text-sm">$100.00</div>
                  </div>
                  <div>
                    <div className="text-xs text-red-800 mb-1">Observed Cost</div>
                    <div className="font-mono text-sm font-bold text-red-600">$105.40</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
              <span className="text-sm text-gray-500">Escalation Policy Triggered: Notify Owner & Pause Agent</span>
              <div className="flex gap-3">
                <button className="px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-lg hover:bg-gray-100 text-sm font-medium">
                  Acknowledge
                </button>
                <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
                  Resolve & Resume
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

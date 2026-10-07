"use client";

import React from 'react';
import Link from 'next/link';

export default function ContractAnalytics() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/contracts" className="text-gray-500 hover:text-gray-700">
          Contracts
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Analytics</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Contract Analytics</h1>
        <p className="text-gray-500 mt-2">Operational metrics based on observed SLA measurements and acceptance history.</p>
      </div>

      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Active Contracts</div>
          <div className="text-3xl font-bold">42</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="text-sm text-green-600 mb-1 font-medium">Completed (30d)</div>
          <div className="text-3xl font-bold">128</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-red-200 bg-red-50">
          <div className="text-sm text-red-600 mb-1 font-medium">SLA Breaches (30d)</div>
          <div className="text-3xl font-bold text-red-700">7</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Unknown Status</div>
          <div className="text-3xl font-bold text-gray-400">2</div>
          <div className="text-xs text-gray-400 mt-1">Missing measurement data</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-4">SLA Breach Breakdown</h3>
          <ul className="space-y-4">
            <li className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Completion Time</span>
              <span className="font-medium">4</span>
            </li>
            <li className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Cost Limit</span>
              <span className="font-medium">2</span>
            </li>
            <li className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Quality Score</span>
              <span className="font-medium">1</span>
            </li>
          </ul>
        </div>
        
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-4">Acceptance Rejections (30d)</h3>
          <div className="flex items-center justify-center h-32 text-sm text-gray-500 bg-gray-50 rounded-lg">
            Observed 12 acceptance failures across 8 contracts.
          </div>
        </div>
      </div>
    </div>
  );
}

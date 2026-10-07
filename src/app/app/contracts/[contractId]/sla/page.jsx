"use client";

import React from 'react';
import Link from 'next/link';

export default function ContractSLAView({ params }) {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/contracts" className="text-gray-500 hover:text-gray-700">
          Contracts
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/contracts/${params?.contractId || 'current'}`} className="text-gray-500 hover:text-gray-700">
          Q4 Competitor Pricing Analysis
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">SLA Details</span>
      </nav>

      <h1 className="text-3xl font-bold mb-8">Service Level Agreements</h1>

      <div className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold mb-1">Completion Time</h3>
                <p className="text-sm text-gray-500">Total elapsed time from activation to acceptance.</p>
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Met
              </span>
            </div>
            
            <div className="grid grid-cols-3 gap-6 mt-6">
              <div>
                <div className="text-xs text-gray-500 mb-1">Target</div>
                <div className="font-medium">&lt; 24.0 hours</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Observed</div>
                <div className="font-medium text-green-600">14.5 hours</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Measurement Source</div>
                <div className="font-medium text-sm">SLA Clock #102</div>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-6 py-3 text-sm text-gray-500">
            Last measured: Oct 10, 2026, 04:20 PM
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold mb-1">Cost Limit</h3>
                <p className="text-sm text-gray-500">Total API and compute costs across all agents.</p>
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                Breached
              </span>
            </div>
            
            <div className="grid grid-cols-3 gap-6 mt-6">
              <div>
                <div className="text-xs text-gray-500 mb-1">Target</div>
                <div className="font-medium">&lt; $100.00</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Observed</div>
                <div className="font-medium text-red-600">$105.40</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Measurement Source</div>
                <div className="font-medium text-sm">Execution Engine (Telemetry)</div>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 px-6 py-3 flex justify-between items-center text-sm">
            <span className="text-gray-500">Breach detected on Oct 11, 2026</span>
            <Link href="/app/contracts/breaches/b-102">
              <span className="text-blue-600 font-medium hover:underline cursor-pointer">View Breach</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

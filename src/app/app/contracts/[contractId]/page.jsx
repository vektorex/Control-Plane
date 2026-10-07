"use client";

import React from 'react';
import Link from 'next/link';

export default function ContractDetail({ params }) {
  // params.contractId
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm">
        <Link href="/app/contracts" className="text-gray-500 hover:text-gray-700">
          Contracts
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Q4 Competitor Pricing Analysis</span>
      </nav>

      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Active
            </span>
            <span className="text-sm font-medium text-gray-500">v2 (Published Oct 1, 2026)</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Q4 Competitor Pricing Analysis</h1>
          <p className="text-gray-500 max-w-2xl">Generate a comprehensive report comparing our pricing tiers against top 5 competitors, including feature-level breakdown.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium">
            Pause
          </button>
          <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
            Edit Contract
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="col-span-2 space-y-6">
          
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <h2 className="font-semibold text-gray-900">Deliverables</h2>
              <Link href={`/app/contracts/${params?.contractId || 'current'}/acceptance`}>
                <span className="text-sm text-blue-600 hover:text-blue-800 font-medium cursor-pointer">View Acceptance Criteria</span>
              </Link>
            </div>
            <div className="p-6">
              <ul className="space-y-4">
                <li className="flex gap-4 items-start">
                  <div className="mt-0.5 text-green-500">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  </div>
                  <div>
                    <h4 className="font-medium">1. Raw Data Extraction</h4>
                    <p className="text-sm text-gray-500 mt-1">Dataset containing raw pricing data scraped from competitor websites.</p>
                    <div className="mt-2 text-xs text-gray-500">Accepted: Oct 5, 2026</div>
                  </div>
                </li>
                <li className="flex gap-4 items-start">
                  <div className="mt-0.5 text-yellow-500">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div>
                    <h4 className="font-medium">2. Final PDF Report</h4>
                    <p className="text-sm text-gray-500 mt-1">Summarized report with citations and markdown tables.</p>
                    <div className="mt-2 text-xs text-gray-500">Due: Oct 15, 2026</div>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <h2 className="font-semibold text-gray-900">Service Level Agreements (SLAs)</h2>
              <Link href={`/app/contracts/${params?.contractId || 'current'}/sla`}>
                <span className="text-sm text-blue-600 hover:text-blue-800 font-medium cursor-pointer">View Details</span>
              </Link>
            </div>
            <div className="p-6 grid grid-cols-2 gap-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-sm font-medium text-gray-900 mb-2">Completion Time</div>
                <div className="flex items-end gap-2 mb-1">
                  <span className="text-2xl font-bold">14.5</span>
                  <span className="text-sm text-gray-500 mb-1">/ 24 hours</span>
                </div>
                <div className="text-xs text-green-600 font-medium">Met (Observed)</div>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-sm font-medium text-gray-900 mb-2">Cost Limit</div>
                <div className="flex items-end gap-2 mb-1">
                  <span className="text-2xl font-bold">$45.00</span>
                  <span className="text-sm text-gray-500 mb-1">/ $100.00</span>
                </div>
                <div className="text-xs text-green-600 font-medium">Met (Observed)</div>
              </div>
            </div>
          </div>
          
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="font-semibold mb-4">Parties</h3>
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="text-gray-500 mb-1">Requester (Human)</dt>
                <dd className="font-medium flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-gray-200"></div>
                  Sarah Jenkins
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 mb-1">Executor (Agent Team)</dt>
                <dd className="font-medium flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-blue-100 text-blue-600 flex items-center justify-center font-bold">RT</div>
                  Research Team Alpha
                </dd>
              </div>
            </dl>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="font-semibold mb-4">Scope Constraints</h3>
            <ul className="space-y-2 text-sm text-gray-600 list-disc pl-4">
              <li>Allowed Workspaces: Marketing</li>
              <li>Required Tools: Browser, PDF Generator</li>
              <li>Data Classification: Public Only</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

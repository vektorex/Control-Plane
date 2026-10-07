"use client";

import React from 'react';
import Link from 'next/link';

export default function ContractAcceptanceView({ params }) {
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
        <span className="text-gray-900">Acceptance Criteria</span>
      </nav>

      <h1 className="text-3xl font-bold mb-8">Acceptance Criteria</h1>

      <div className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold">1. Data Grounding Required</h3>
              <p className="text-sm text-gray-500 mt-1">All claims in the report must be backed by retrieved sources.</p>
            </div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Passed
            </span>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-700"><span className="font-semibold">Evidence:</span> Evaluation Lab execution #EV-992 passed with 100% factual consistency score.</p>
            <p className="text-xs text-gray-500 mt-2">Verified automatically at Oct 10, 2026, 04:00 PM</p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold">2. PDF Format</h3>
              <p className="text-sm text-gray-500 mt-1">The final deliverable must be a correctly formatted PDF document.</p>
            </div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              Pending
            </span>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-700">Awaiting file submission.</p>
            </div>
            <button className="px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-lg hover:bg-gray-100 text-sm font-medium">
              Manual Verification
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

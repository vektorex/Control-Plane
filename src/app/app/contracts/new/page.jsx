"use client";

import React from 'react';
import Link from 'next/link';

export default function NewContract() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/contracts" className="text-gray-500 hover:text-gray-700">
          Contracts
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">New Contract</span>
      </nav>

      <h1 className="text-3xl font-bold mb-8">Draft Work Contract</h1>

      <div className="space-y-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <h2 className="text-xl font-semibold mb-6">Basic Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contract Name</label>
              <input type="text" className="w-full p-2 border border-gray-300 rounded-md" placeholder="e.g. Q4 Competitor Analysis" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Objective Link (Optional)</label>
              <select className="w-full p-2 border border-gray-300 rounded-md">
                <option>None</option>
                <option>Increase Market Share (OBJ-12)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Assigned Resource</label>
              <select className="w-full p-2 border border-gray-300 rounded-md">
                <option>Select Agent or Team</option>
                <option>Research Team Alpha</option>
                <option>Data Extraction Agent v2</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Service Level Agreements</h2>
            <button className="text-sm text-blue-600 font-medium">Add SLA +</button>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg mb-4 bg-gray-50">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Metric</label>
                <select className="w-full p-2 text-sm border border-gray-300 rounded-md">
                  <option>Completion Time</option>
                  <option>Cost Limit</option>
                  <option>Quality Score</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Target</label>
                <input type="number" className="w-full p-2 text-sm border border-gray-300 rounded-md" placeholder="24" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Unit</label>
                <select className="w-full p-2 text-sm border border-gray-300 rounded-md">
                  <option>hours</option>
                  <option>USD</option>
                </select>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex justify-end gap-4">
          <Link href="/app/contracts">
            <button className="px-6 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50">Cancel</button>
          </Link>
          <button className="px-6 py-2 bg-black text-white rounded-lg font-medium hover:bg-gray-800">Propose Contract</button>
        </div>
      </div>
    </div>
  );
}

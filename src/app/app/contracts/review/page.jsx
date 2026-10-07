"use client";

import React from 'react';
import Link from 'next/link';

export default function ContractReview() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/contracts" className="text-gray-500 hover:text-gray-700">
          Contracts
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Review</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Contract Review</h1>
        <p className="text-gray-500 mt-2">Approve or reject proposed work contracts before they become active.</p>
      </div>

      <div className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-start mb-6">
              <div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mb-2">
                  Review Required
                </span>
                <h3 className="text-xl font-bold">Customer Data Analysis Workflow</h3>
                <p className="text-sm text-gray-500 mt-1">Proposed by: Automation Engine</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-8">
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Scope & Resources</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li><span className="font-medium text-gray-800">Resource:</span> Data Analysis Agent Team</li>
                  <li><span className="font-medium text-gray-800">Data Access:</span> Customer Support DB (Read Only)</li>
                  <li><span className="font-medium text-gray-800">Classification:</span> Confidential</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Service Level Agreements</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li><span className="font-medium text-gray-800">Completion Target:</span> &lt; 4 hours</li>
                  <li><span className="font-medium text-gray-800">Compute Budget:</span> &lt; $50.00</li>
                </ul>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-semibold text-yellow-800 mb-2">Governance Warning</h4>
              <p className="text-sm text-yellow-700">This contract requests access to Confidential data. It requires explicit approval from a Data Steward before activation.</p>
            </div>
          </div>
          <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
            <span className="text-sm text-gray-500">Approvals required: 1 / 1</span>
            <div className="flex gap-3">
              <button className="px-6 py-2 border border-gray-300 bg-white text-gray-700 rounded-lg hover:bg-gray-100 font-medium">
                Reject
              </button>
              <button className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 font-medium">
                Approve & Activate
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

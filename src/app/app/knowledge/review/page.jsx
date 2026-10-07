"use client";

import React from 'react';
import Link from 'next/link';

export default function KnowledgeReviewQueue() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/knowledge" className="text-gray-500 hover:text-gray-700">
          Organizational Knowledge
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Review Queue</span>
      </nav>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Review Queue</h1>
          <p className="text-gray-500 mt-2">Evaluate and verify knowledge candidates proposed by AI and Agents.</p>
        </div>
      </div>

      <div className="space-y-6">
        {[1, 2].map((candidate) => (
          <div key={candidate} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mb-2">
                    Pending Review
                  </span>
                  <h3 className="text-lg font-semibold">
                    Always retry transient 5xx errors for Stripe API
                  </h3>
                </div>
                <span className="text-xs text-gray-500">Extracted 2 hours ago</span>
              </div>
              <div className="text-sm text-gray-600 space-y-4">
                <p>
                  <strong>Proposed Content:</strong> Transient errors from the Stripe API (502, 503, 504) should be retried using exponential backoff to prevent payment failures during brief outages.
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="font-medium mb-2">Source Evidence:</p>
                  <p className="text-gray-500 italic">"The payment workflow failed because we didn't retry a 503 from Stripe. I updated the workflow to include an exponential backoff retry policy for 5xx errors."</p>
                  <p className="text-xs text-gray-400 mt-2">— Incident Postmortem #402</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
              <div className="flex gap-2">
                <span className="text-xs text-gray-500 px-2 py-1 bg-white border border-gray-200 rounded">Scope: Workspace</span>
                <span className="text-xs text-gray-500 px-2 py-1 bg-white border border-gray-200 rounded">Type: Lesson</span>
              </div>
              <div className="flex gap-3">
                <button className="px-4 py-2 border border-gray-200 bg-white text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium">
                  Reject
                </button>
                <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
                  Accept & Verify
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

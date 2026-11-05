"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function KnowledgeReviewQueue() {
  const [candidates, setCandidates] = useState([
    {
      id: 1,
      title: "Always retry transient 5xx errors for Stripe API",
      time: "Extracted 2 hours ago",
      content: "Transient errors from the Stripe API (502, 503, 504) should be retried using exponential backoff to prevent payment failures during brief outages.",
      evidence: "The payment workflow failed because we didn't retry a 503 from Stripe. I updated the workflow to include an exponential backoff retry policy for 5xx errors.",
      source: "Incident Postmortem #402",
      scope: "Workspace",
      type: "Lesson",
      status: "pending"
    },
    {
      id: 2,
      title: "Postgres Connection Pool Timeout Cap",
      time: "Extracted 5 hours ago",
      content: "Ensure database connection timeout is configured to a maximum of 15 seconds to prevent thread starvation under heavy load.",
      evidence: "High connection latency caused backend starvation during peak traffic.",
      source: "Architecture Decision Record #014",
      scope: "Workspace",
      type: "Policy",
      status: "pending"
    }
  ]);

  const handleAction = (id, action) => {
    setCandidates((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: action } : c))
    );
  };

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
        {candidates.map((candidate) => (
          <div key={candidate.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mb-2 ${
                    candidate.status === 'accepted' 
                      ? 'bg-green-100 text-green-800'
                      : candidate.status === 'rejected'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {candidate.status === 'accepted' ? 'Accepted & Verified' : candidate.status === 'rejected' ? 'Rejected' : 'Pending Review'}
                  </span>
                  <h3 className="text-lg font-semibold">
                    {candidate.title}
                  </h3>
                </div>
                <span className="text-xs text-gray-500">{candidate.time}</span>
              </div>
              <div className="text-sm text-gray-600 space-y-4">
                <p>
                  <strong>Proposed Content:</strong> {candidate.content}
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="font-medium mb-2">Source Evidence:</p>
                  <p className="text-gray-500 italic">"{candidate.evidence}"</p>
                  <p className="text-xs text-gray-400 mt-2">— {candidate.source}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
              <div className="flex gap-2">
                <span className="text-xs text-gray-500 px-2 py-1 bg-white border border-gray-200 rounded">Scope: {candidate.scope}</span>
                <span className="text-xs text-gray-500 px-2 py-1 bg-white border border-gray-200 rounded">Type: {candidate.type}</span>
              </div>
              <div className="flex gap-3">
                {candidate.status === 'pending' ? (
                  <>
                    <button 
                      onClick={() => handleAction(candidate.id, 'rejected')}
                      className="px-4 py-2 border border-gray-200 bg-white text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium cursor-pointer"
                    >
                      Reject
                    </button>
                    <button 
                      onClick={() => handleAction(candidate.id, 'accepted')}
                      className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium cursor-pointer"
                    >
                      Accept & Verify
                    </button>
                  </>
                ) : (
                  <span className="text-sm font-medium text-gray-500">
                    Decision recorded: {candidate.status}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

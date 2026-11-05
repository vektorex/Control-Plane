"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function ContractBreaches() {
  const [breaches, setBreaches] = useState([
    { id: 1, name: "Cost Limit Exceeded", expected: "$100.00", observed: "$105.40", status: "Open Breach", severity: "Major", contractId: "CTR-8811" },
    { id: 2, name: "Latency SLA Exceeded", expected: "2500ms", observed: "3200ms", status: "Open Breach", severity: "Minor", contractId: "CTR-8812" }
  ]);

  const handleAcknowledge = (id) => {
    setBreaches(prev => prev.map(b => b.id === id ? { ...b, status: "Acknowledged" } : b));
  };

  const handleResolve = (id) => {
    setBreaches(prev => prev.filter(b => b.id !== id));
  };

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
        {breaches.length === 0 ? (
          <div className="p-8 text-center text-gray-500 bg-white border border-gray-200 rounded-xl">
            No active contract breaches detected. All systems operating within SLA bounds.
          </div>
        ) : (
          breaches.map((breach) => (
            <div key={breach.id} className="bg-white border border-red-200 rounded-xl overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        breach.status === "Acknowledged" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
                      }`}>
                        {breach.status}
                      </span>
                      <span className="text-sm font-medium text-gray-500">Severity: {breach.severity}</span>
                    </div>
                    <h3 className="text-lg font-semibold">{breach.name}</h3>
                    <Link href={`/app/contracts/${breach.contractId}`}>
                      <span className="text-sm text-blue-600 hover:underline">Contract #{breach.contractId}</span>
                    </Link>
                  </div>
                  <span className="text-sm text-gray-500">Detected Oct 11, 2026</span>
                </div>
                
                <div className="bg-red-50 p-4 rounded-lg mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-red-800 mb-1">Expected Limit</div>
                      <div className="font-mono text-sm">{breach.expected}</div>
                    </div>
                    <div>
                      <div className="text-xs text-red-800 mb-1">Observed Metric</div>
                      <div className="font-mono text-sm font-bold text-red-600">{breach.observed}</div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
                <span className="text-sm text-gray-500">Escalation Policy Triggered: Notify Owner & Pause Agent</span>
                <div className="flex gap-3">
                  {breach.status !== "Acknowledged" && (
                    <button 
                      type="button"
                      onClick={() => handleAcknowledge(breach.id)}
                      className="px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-lg hover:bg-gray-100 text-sm font-medium cursor-pointer"
                    >
                      Acknowledge
                    </button>
                  )}
                  <button 
                    type="button"
                    onClick={() => handleResolve(breach.id)}
                    className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium cursor-pointer"
                  >
                    Resolve & Resume
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

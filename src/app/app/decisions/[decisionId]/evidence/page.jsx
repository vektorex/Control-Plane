"use client";

import React from 'react';
import Link from 'next/link';

export default function EvidenceView({ params }) {
  // params.decisionId
  
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/decisions" className="text-gray-500 hover:text-gray-700">
          Decision Intelligence
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/decisions/${params.decisionId}`} className="text-gray-500 hover:text-gray-700">
          {params.decisionId}
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Collected Evidence</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Evidence Provenance</h1>
        <p className="text-gray-500 mt-2">The deterministic facts collected at evaluation time that support this decision.</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="p-4 font-semibold text-gray-700">Source Type</th>
              <th className="p-4 font-semibold text-gray-700">Claim / Value</th>
              <th className="p-4 font-semibold text-gray-700">Status</th>
              <th className="p-4 font-semibold text-gray-700">Freshness</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            <tr>
              <td className="p-4">
                <div className="font-medium text-gray-900">Governance Policy</div>
                <div className="text-xs text-gray-500">ID: gov-confidential</div>
              </td>
              <td className="p-4 text-gray-700">
                Rule: "Approval required for Confidential Data."
              </td>
              <td className="p-4"><span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded border border-blue-200">Observed</span></td>
              <td className="p-4 text-gray-500 text-xs">2 mins ago</td>
            </tr>
            <tr>
              <td className="p-4">
                <div className="font-medium text-gray-900">Reliability Monitor</div>
                <div className="text-xs text-gray-500">ID: mon-pdf-ext</div>
              </td>
              <td className="p-4 text-gray-700">
                State: 503 Degraded
              </td>
              <td className="p-4"><span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded border border-blue-200">Observed</span></td>
              <td className="p-4 text-gray-500 text-xs">1 min ago</td>
            </tr>
            <tr>
              <td className="p-4">
                <div className="font-medium text-gray-900">Security Scan</div>
                <div className="text-xs text-gray-500">ID: sec-scan-88</div>
              </td>
              <td className="p-4 text-gray-700">
                Incidents: 0 Active
              </td>
              <td className="p-4"><span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded border border-green-200">Verified</span></td>
              <td className="p-4 text-gray-500 text-xs">5 mins ago</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

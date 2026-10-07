"use client";

import React from 'react';
import Link from 'next/link';

export default function ReadinessView({ params }) {
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
        <span className="text-gray-900">Readiness Factors</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Readiness Evaluation</h1>
        <p className="text-gray-500 mt-2">Deterministic evaluation of all conditions required for execution.</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="p-4 font-semibold text-gray-700">Condition Factor</th>
              <th className="p-4 font-semibold text-gray-700">Rule Applied</th>
              <th className="p-4 font-semibold text-gray-700">State</th>
              <th className="p-4 font-semibold text-gray-700">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            <tr>
              <td className="p-4 font-medium text-gray-900">Security Clearance</td>
              <td className="p-4 text-gray-600">No active blocking security incidents on target resources.</td>
              <td className="p-4"><span className="text-green-600 font-medium">Satisfied</span></td>
              <td className="p-4 text-gray-500">Security Module (STEP 34)</td>
            </tr>
            <tr>
              <td className="p-4 font-medium text-gray-900">Data Governance</td>
              <td className="p-4 text-gray-600">Confidential data flows must have explicit approval.</td>
              <td className="p-4"><span className="text-red-600 font-medium">Unsatisfied</span></td>
              <td className="p-4 text-gray-500">Data Policy #DP-902</td>
            </tr>
            <tr>
              <td className="p-4 font-medium text-gray-900">Dependency Health</td>
              <td className="p-4 text-gray-600">All mandatory components must report HEALTHY.</td>
              <td className="p-4"><span className="text-red-600 font-medium">Unsatisfied</span></td>
              <td className="p-4 text-gray-500">Reliability Monitor #mon-pdf-ext</td>
            </tr>
            <tr>
              <td className="p-4 font-medium text-gray-900">Evaluation Compliance</td>
              <td className="p-4 text-gray-600">Models used must be certified for this use case.</td>
              <td className="p-4"><span className="text-green-600 font-medium">Satisfied</span></td>
              <td className="p-4 text-gray-500">Eval Lab Certification #cert-gpt4-sec</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

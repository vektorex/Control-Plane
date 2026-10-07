"use client";

import React from 'react';
import Link from 'next/link';

export default function KnowledgeFreshness() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/knowledge" className="text-gray-500 hover:text-gray-700">
          Organizational Knowledge
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Freshness Report</span>
      </nav>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Freshness Report</h1>
          <p className="text-gray-500 mt-2">Identify aging and stale knowledge that requires re-verification.</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Total Verified</div>
          <div className="text-3xl font-bold">142</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="text-sm text-green-600 mb-1 font-medium">Fresh (0-90 days)</div>
          <div className="text-3xl font-bold">89</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200">
          <div className="text-sm text-yellow-600 mb-1 font-medium">Aging (90-180 days)</div>
          <div className="text-3xl font-bold">41</div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-red-200 bg-red-50">
          <div className="text-sm text-red-600 mb-1 font-medium">Stale (&gt;180 days)</div>
          <div className="text-3xl font-bold text-red-700">12</div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Knowledge Item
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reason
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            <tr>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="font-medium text-sm text-gray-900">OAuth Provider Configuration</div>
                <div className="text-xs text-gray-500">Security Rule</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  Stale
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="text-sm text-gray-900">Source policy was modified 3 days ago.</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button className="text-blue-600 hover:text-blue-900">Re-verify</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

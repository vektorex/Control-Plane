"use client";

import React from 'react';
import Link from 'next/link';

export default function CatalogCompare() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/catalog" className="text-gray-500 hover:text-gray-700">
          Catalog
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Compare</span>
      </nav>

      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold">Compare Capabilities</h1>
          <p className="text-gray-500 mt-2">Factually compare up to 4 catalog items side-by-side.</p>
        </div>
        <button className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-sm hover:bg-gray-50">
          + Add Item
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr>
              <th className="p-4 border-b border-gray-200 bg-gray-50 w-64">Attribute</th>
              <th className="p-4 border-b border-gray-200 w-1/2">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 mb-2">Agent Team</span>
                    <h3 className="font-bold text-lg">Deep Research Team Alpha</h3>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">✕</button>
                </div>
              </th>
              <th className="p-4 border-b border-gray-200 w-1/2">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mb-2">Workflow</span>
                    <h3 className="font-bold text-lg">Customer Onboarding Extraction</h3>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">✕</button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="text-sm">
            <tr>
              <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Category</td>
              <td className="p-4 border-b border-gray-200">Research & Analysis</td>
              <td className="p-4 border-b border-gray-200">Data & Operations</td>
            </tr>
            <tr>
              <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Supported Modalities</td>
              <td className="p-4 border-b border-gray-200">
                <div className="flex gap-2"><span className="px-2 py-1 bg-gray-100 rounded text-xs">Text</span><span className="px-2 py-1 bg-gray-100 rounded text-xs">Data</span></div>
              </td>
              <td className="p-4 border-b border-gray-200">
                <div className="flex gap-2"><span className="px-2 py-1 bg-gray-100 rounded text-xs">Text</span><span className="px-2 py-1 bg-gray-100 rounded text-xs">Image (OCR)</span></div>
              </td>
            </tr>
            <tr>
              <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Required Approvals</td>
              <td className="p-4 border-b border-gray-200 text-gray-500">None</td>
              <td className="p-4 border-b border-gray-200 text-amber-600 font-medium">Data Steward Approval (Confidential)</td>
            </tr>
            <tr>
              <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Availability</td>
              <td className="p-4 border-b border-gray-200">
                <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-500"></div> Available</span>
              </td>
              <td className="p-4 border-b border-gray-200">
                <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-gray-400"></div> Unknown</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

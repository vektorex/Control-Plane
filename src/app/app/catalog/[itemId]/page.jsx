"use client";

import React from 'react';
import Link from 'next/link';

export default function CatalogDetailView({ params }) {
  // params.itemId
  
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/catalog" className="text-gray-500 hover:text-gray-700">
          Catalog
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Deep Research Team Alpha</span>
      </nav>

      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              Agent Team
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Available
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Eligible
            </span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Deep Research Team Alpha</h1>
          <p className="text-gray-500 max-w-2xl text-lg">A specialized team of agents configured to scrape, synthesize, and cite sources for deep market research.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 font-medium">
            Use in Workflow
          </button>
          <Link href="/app/contracts/new">
            <button className="px-4 py-2 border border-gray-200 bg-white text-black rounded-lg hover:bg-gray-50 font-medium">
              Create Contract
            </button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="col-span-2 space-y-8">
          
          <section>
            <h2 className="text-xl font-bold mb-4">Capabilities</h2>
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <div className="mt-1 text-blue-600"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Semantic Web Search</h4>
                    <p className="text-sm text-gray-600 mt-1">Executes iterative web searches to find non-obvious market data.</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="mt-1 text-blue-600"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div>
                  <div>
                    <h4 className="font-semibold text-gray-900">Data Synthesis & Citation</h4>
                    <p className="text-sm text-gray-600 mt-1">Aggregates findings into a structured report, linking every claim to its source URL.</p>
                  </div>
                </li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-4">Input & Output Schema</h2>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="grid grid-cols-2">
                <div className="p-6 border-r border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg>
                    Expected Inputs
                  </h4>
                  <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-600 overflow-x-auto">
{`{
  "query": "string (required)",
  "competitors": ["string"],
  "depth": "enum(shallow, deep)"
}`}
                  </pre>
                </div>
                <div className="p-6">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
                    Produces Outputs
                  </h4>
                  <pre className="bg-gray-50 p-4 rounded-lg text-xs text-gray-600 overflow-x-auto">
{`{
  "report_markdown": "string",
  "citations": [
    {
      "claim": "string",
      "url": "string"
    }
  ]
}`}
                  </pre>
                </div>
              </div>
            </div>
          </section>
          
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Governance & Requirements</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Data Class Allowed</span>
                <span className="font-medium text-gray-900">Public, Internal</span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Required Approval</span>
                <span className="font-medium text-gray-900">None</span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Supported Modalities</span>
                <span className="font-medium text-gray-900">Text, Data</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Metadata</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between">
                <span className="text-gray-500">Owner</span>
                <span className="font-medium text-gray-900">Data Science Org</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-500">Version</span>
                <span className="font-medium text-gray-900">v2.4.0</span>
              </li>
              <li className="flex justify-between">
                <span className="text-gray-500">Last Synced</span>
                <span className="font-medium text-gray-900 flex items-center gap-1">
                  Oct 10, 2026
                  <span className="w-2 h-2 rounded-full bg-green-500 ml-1" title="Fresh"></span>
                </span>
              </li>
            </ul>
            <div className="mt-6">
              <button className="w-full py-2 border border-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors">
                View Source Resource ↗
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

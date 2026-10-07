"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function CatalogDiscovery() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Service Catalog</h1>
          <p className="text-gray-500 mt-2">Discover and consume governed AI capabilities across your organization.</p>
        </div>
        <div className="flex gap-4">
          <Link href="/app/catalog/settings">
            <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium bg-white">
              Catalog Settings
            </button>
          </Link>
          <Link href="/app/catalog/compare">
            <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
              Compare Capabilities
            </button>
          </Link>
        </div>
      </div>

      <div className="mb-8 relative">
        <input 
          type="text" 
          placeholder="Search for capabilities (e.g. 'PDF analysis', 'Security review')..." 
          className="w-full p-4 pl-12 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <svg className="w-6 h-6 text-gray-400 absolute left-4 top-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </div>

      <div className="flex gap-8">
        {/* Sidebar Filters */}
        <div className="w-64 flex-shrink-0 space-y-6">
          <div>
            <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-gray-500">Resource Type</h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded text-blue-600" /> Workflows</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded text-blue-600" /> Agent Teams</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded text-blue-600" /> Standalone Agents</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded text-blue-600" /> Document Capabilities</label>
            </div>
          </div>
          <div>
            <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-gray-500">Eligibility</h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded text-blue-600" defaultChecked /> Eligible for Me</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded text-blue-600" /> Requires Approval</label>
            </div>
          </div>
          <div>
            <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-gray-500">Categories</h3>
            <div className="space-y-2">
              <Link href="/app/catalog/capabilities"><span className="text-sm text-blue-600 hover:underline cursor-pointer">Browse All Categories →</span></Link>
            </div>
          </div>
        </div>

        {/* Catalog Grid */}
        <div className="flex-1">
          <div className="grid grid-cols-2 gap-6">
            
            {/* Mock Item 1 */}
            <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
              <div className="flex justify-between items-start mb-3">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                  Agent Team
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                  Available
                </span>
              </div>
              <Link href="/app/catalog/cat-team-research">
                <h3 className="text-lg font-bold hover:text-blue-600 mb-1">Deep Research Team Alpha</h3>
              </Link>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">A specialized team of agents configured to scrape, synthesize, and cite sources for deep market research.</p>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-xs border border-gray-200 bg-gray-50 px-2 py-1 rounded">Web Search</span>
                <span className="text-xs border border-gray-200 bg-gray-50 px-2 py-1 rounded">PDF Parsing</span>
                <span className="text-xs border border-gray-200 bg-gray-50 px-2 py-1 rounded">Citation Gen</span>
              </div>
              <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
                <span>By: Data Science Org</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-500"></div> Fresh</span>
              </div>
            </div>

            {/* Mock Item 2 */}
            <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
              <div className="flex justify-between items-start mb-3">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  Workflow
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                  Approval Req.
                </span>
              </div>
              <Link href="/app/catalog/cat-wf-onboarding">
                <h3 className="text-lg font-bold hover:text-blue-600 mb-1">Customer Onboarding Extraction</h3>
              </Link>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">Extracts structured entity data from raw customer onboarding emails and attachments.</p>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-xs border border-gray-200 bg-gray-50 px-2 py-1 rounded">JSON Output</span>
                <span className="text-xs border border-gray-200 bg-gray-50 px-2 py-1 rounded">PII Redaction</span>
              </div>
              <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
                <span>By: Operations Team</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-gray-300"></div> Unknown</span>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

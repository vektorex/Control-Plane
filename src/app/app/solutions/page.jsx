"use client";

import React from 'react';
import Link from 'next/link';

export default function SolutionsDiscovery() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Solutions</h1>
          <p className="text-gray-500 mt-2">Discover, compose, and manage governed AI work solutions.</p>
        </div>
        <div className="flex gap-4">
          <Link href="/app/solutions/templates">
            <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium bg-white">
              Templates
            </button>
          </Link>
          <Link href="/app/solutions/new">
            <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
              Create Solution
            </button>
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <a href="#" className="border-b-2 border-black py-4 px-1 text-sm font-medium text-black">My Solutions</a>
          <a href="#" className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 border-b-2 py-4 px-1 text-sm font-medium">Published</a>
          <a href="#" className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 border-b-2 py-4 px-1 text-sm font-medium">Needs Review (1)</a>
        </nav>
      </div>

      <div className="grid grid-cols-3 gap-6">
        
        {/* Mock Solution 1 */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
          <div className="flex justify-between items-start mb-3">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
              Published
            </span>
            <span className="text-xs text-gray-500 font-medium">v2.1.0</span>
          </div>
          <Link href="/app/solutions/sol-github-sec">
            <h3 className="text-lg font-bold hover:text-blue-600 mb-1">Automated GitHub Security Review</h3>
          </Link>
          <p className="text-sm text-gray-500 mb-4 line-clamp-2">Composes repository discovery, code analysis, and human approval to generate automated security reports.</p>
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
              4 Components
            </span>
          </div>
          <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
            <span>By: Security Team</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-500"></div> Valid</span>
          </div>
        </div>

        {/* Mock Solution 2 */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
          <div className="flex justify-between items-start mb-3">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
              Draft
            </span>
            <span className="text-xs text-gray-500 font-medium">v0.1.0</span>
          </div>
          <Link href="/app/solutions/sol-doc-intel">
            <h3 className="text-lg font-bold hover:text-blue-600 mb-1">Customer Contract Analyzer</h3>
          </Link>
          <p className="text-sm text-gray-500 mb-4 line-clamp-2">Extracts clauses, liabilities, and SLAs from uploaded PDF contracts.</p>
          <div className="flex flex-wrap gap-2 mb-4">
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
              2 Components
            </span>
          </div>
          <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
            <span>By: You</span>
            <span className="flex items-center gap-1 text-amber-600"><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg> Validation Error</span>
          </div>
        </div>

      </div>
    </div>
  );
}

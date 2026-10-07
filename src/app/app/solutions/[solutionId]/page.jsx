"use client";

import React from 'react';
import Link from 'next/link';

export default function SolutionDetailView({ params }) {
  // params.solutionId
  
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/solutions" className="text-gray-500 hover:text-gray-700">
          Solutions
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Automated GitHub Security Review</span>
      </nav>

      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Published
            </span>
            <span className="text-sm font-medium text-gray-500">v2.1.0</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Automated GitHub Security Review</h1>
          <p className="text-gray-500 max-w-2xl text-lg">Composes repository discovery, code analysis, and human approval to generate automated security reports.</p>
        </div>
        <div className="flex gap-3">
          <Link href={`/app/solutions/${params.solutionId}/simulate`}>
            <button className="px-4 py-2 border border-gray-200 bg-white text-black rounded-lg hover:bg-gray-50 font-medium">
              Simulate Run
            </button>
          </Link>
          <Link href={`/app/solutions/${params.solutionId}/builder`}>
            <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 font-medium">
              Open Builder
            </button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="col-span-2 space-y-8">
          
          <section>
            <h2 className="text-xl font-bold mb-4">Inputs & Outputs</h2>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="grid grid-cols-2">
                <div className="p-6 border-r border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg>
                    Required Inputs
                  </h4>
                  <ul className="space-y-3">
                    <li className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900">repository_url</span>
                      <span className="text-xs text-gray-500">String • Must be a valid GitHub URL</span>
                    </li>
                    <li className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900">branch</span>
                      <span className="text-xs text-gray-500">String • Defaults to 'main'</span>
                    </li>
                  </ul>
                </div>
                <div className="p-6">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
                    Produced Outputs
                  </h4>
                  <ul className="space-y-3">
                    <li className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900">security_report</span>
                      <span className="text-xs text-gray-500">Document (PDF/Markdown)</span>
                    </li>
                    <li className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900">vulnerabilities_json</span>
                      <span className="text-xs text-gray-500">Structured Data • Requires Validation Evidence</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Capabilities Used</h2>
              <Link href={`/app/solutions/${params.solutionId}/dependencies`} className="text-sm text-blue-600 hover:underline">View Dependency Tree</Link>
            </div>
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <ul className="space-y-4">
                <li className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">Connector</span>
                    <span className="font-medium">GitHub Repository Extractor</span>
                  </div>
                  <span className="text-xs text-green-600 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-600"></div> Available</span>
                </li>
                <li className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs">Agent Team</span>
                    <span className="font-medium">Static Code Analysis Team</span>
                  </div>
                  <span className="text-xs text-green-600 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-600"></div> Available</span>
                </li>
                <li className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-xs">Approval</span>
                    <span className="font-medium">Security Lead Sign-off</span>
                  </div>
                  <span className="text-xs text-gray-500">HITL Checkpoint</span>
                </li>
                <li className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">Workflow</span>
                    <span className="font-medium">PDF Report Generator</span>
                  </div>
                  <span className="text-xs text-green-600 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-600"></div> Available</span>
                </li>
              </ul>
            </div>
          </section>
          
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Governance</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">Data Classification</span>
                <span className="font-medium text-gray-900">Confidential</span>
              </li>
              <li className="flex justify-between py-1 border-b border-gray-100">
                <span className="text-gray-500">External Connectors</span>
                <span className="font-medium text-gray-900">1 (GitHub)</span>
              </li>
              <li className="flex justify-between py-1">
                <span className="text-gray-500">HITL Required</span>
                <span className="font-medium text-gray-900">Yes</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-bold text-gray-900 mb-4">Instantiation</h3>
            <p className="text-sm text-gray-600 mb-4">This solution can be instantiated as a managed run.</p>
            <button className="w-full py-2 bg-black text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors">
              Instantiate in Workflow Engine
            </button>
            <button className="w-full py-2 mt-2 border border-gray-300 text-black text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors">
              Add to Work Plan
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

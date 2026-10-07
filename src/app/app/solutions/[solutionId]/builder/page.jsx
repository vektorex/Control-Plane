"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function SolutionBuilder({ params }) {
  // params.solutionId
  
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      
      {/* Left Palette */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <Link href={`/app/solutions/${params.solutionId}`} className="text-sm text-gray-500 hover:text-gray-900 mb-4 inline-block">
            ← Back to Solution
          </Link>
          <h2 className="font-bold text-lg">Capabilities Palette</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Service Catalog</h3>
            <div className="space-y-2">
              <div className="p-3 border border-gray-200 rounded-lg bg-gray-50 cursor-grab hover:border-blue-400 flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-purple-100 text-purple-700 flex items-center justify-center text-xs">A</span>
                <span className="text-sm font-medium">Agent Team</span>
              </div>
              <div className="p-3 border border-gray-200 rounded-lg bg-gray-50 cursor-grab hover:border-blue-400 flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-blue-100 text-blue-700 flex items-center justify-center text-xs">W</span>
                <span className="text-sm font-medium">Workflow</span>
              </div>
              <div className="p-3 border border-gray-200 rounded-lg bg-gray-50 cursor-grab hover:border-blue-400 flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-orange-100 text-orange-700 flex items-center justify-center text-xs">C</span>
                <span className="text-sm font-medium">Connector</span>
              </div>
            </div>
            <button className="w-full mt-3 py-2 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50">
              Search Catalog...
            </button>
          </div>

          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Control Nodes</h3>
            <div className="space-y-2">
              <div className="p-3 border border-gray-200 rounded-lg bg-white cursor-grab hover:border-blue-400 flex items-center gap-2">
                <span className="text-sm font-medium">Human Approval</span>
              </div>
              <div className="p-3 border border-gray-200 rounded-lg bg-white cursor-grab hover:border-blue-400 flex items-center gap-2">
                <span className="text-sm font-medium">Evaluation Check</span>
              </div>
            </div>
          </div>
          
        </div>
      </div>

      {/* Center Canvas */}
      <div className="flex-1 flex flex-col relative bg-slate-50">
        <div className="absolute top-4 left-4 bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm flex items-center gap-4 z-10">
          <span className="font-semibold text-sm">Automated GitHub Security Review</span>
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">Draft</span>
        </div>
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <button className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">Save Draft</button>
          <button className="px-4 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800">Submit for Review</button>
        </div>

        {/* Mock Canvas Area */}
        <div className="flex-1 w-full h-full relative overflow-hidden flex items-center justify-center bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-90">
          {/* Mock Node */}
          <div className="absolute top-1/4 left-1/3 bg-white border-2 border-blue-500 rounded-xl shadow-lg w-64 z-20">
            <div className="px-4 py-2 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-xl">
              <span className="text-xs font-semibold text-blue-600">Connector</span>
            </div>
            <div className="p-4">
              <h4 className="font-bold text-gray-900 text-sm mb-1">GitHub Repo Extractor</h4>
              <p className="text-xs text-gray-500">Extracts source code from URL</p>
            </div>
            {/* Ports */}
            <div className="absolute -left-2 top-1/2 w-4 h-4 bg-white border-2 border-gray-300 rounded-full"></div>
            <div className="absolute -right-2 top-1/2 w-4 h-4 bg-white border-2 border-blue-500 rounded-full"></div>
          </div>
          
          <div className="absolute top-1/3 left-1/2 w-32 border-t-2 border-dashed border-gray-400 z-10"></div>

          {/* Mock Node 2 */}
          <div className="absolute top-1/4 right-1/4 bg-white border border-gray-200 rounded-xl shadow-md w-64 z-20 opacity-80 hover:opacity-100 cursor-pointer">
            <div className="px-4 py-2 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-xl">
              <span className="text-xs font-semibold text-purple-600">Agent Team</span>
            </div>
            <div className="p-4">
              <h4 className="font-bold text-gray-900 text-sm mb-1">Security Analysis Team</h4>
              <p className="text-xs text-gray-500">Reviews code for vulnerabilities</p>
            </div>
            {/* Ports */}
            <div className="absolute -left-2 top-1/2 w-4 h-4 bg-white border-2 border-gray-300 rounded-full"></div>
            <div className="absolute -right-2 top-1/2 w-4 h-4 bg-white border-2 border-gray-300 rounded-full"></div>
          </div>

        </div>

        {/* Bottom Validation Panel */}
        <div className="h-48 bg-white border-t border-gray-200">
          <div className="flex border-b border-gray-100">
            <button className="px-6 py-3 border-b-2 border-blue-500 text-blue-600 font-medium text-sm">Validation Issues (1)</button>
            <button className="px-6 py-3 text-gray-500 font-medium text-sm">Requirements</button>
            <button className="px-6 py-3 text-gray-500 font-medium text-sm">Governance</button>
          </div>
          <div className="p-4 overflow-y-auto h-[calc(100%-45px)]">
            <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-100 rounded-lg">
              <svg className="w-5 h-5 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <div>
                <h4 className="text-sm font-semibold text-red-800">Missing Required Output Mapping</h4>
                <p className="text-xs text-red-600 mt-1">The solution output "security_report" is not connected to any component output port.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Inspector */}
      <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-bold text-lg">Configuration</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">GitHub Repo Extractor</h3>
            <p className="text-xs text-gray-500 mb-4">Catalog Reference: #cat-gh-123</p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Component Key</label>
                <input type="text" className="w-full p-2 border border-gray-300 rounded text-sm bg-gray-50" defaultValue="repo_extractor" readOnly />
              </div>
              
              <div className="border-t border-gray-100 pt-4">
                <h4 className="text-xs font-semibold text-gray-900 mb-2">Input Mapping</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-medium text-gray-700">url (required)</span>
                    <span className="text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">solution.inputs.repo_url</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-medium text-gray-700">branch</span>
                    <span className="text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">solution.inputs.branch</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}

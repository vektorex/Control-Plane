"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function IntentWorkspace() {
  const [intent, setIntent] = useState('');

  return (
    <div className="p-6 max-w-5xl mx-auto h-screen flex flex-col">
      <div className="mb-10 text-center mt-12">
        <h1 className="text-4xl font-bold mb-4">What do you want to build?</h1>
        <p className="text-gray-500 text-lg max-w-2xl mx-auto">
          Describe your objective in plain English. We will analyze requirements, discover governed capabilities, and synthesize candidate solutions for your review.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden mb-12">
        <textarea 
          className="w-full h-40 p-6 text-lg focus:outline-none resize-none"
          placeholder="e.g. 'Review this GitHub repository for security vulnerabilities and create a verified report for the management team...'"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
        ></textarea>
        <div className="bg-gray-50 p-4 border-t border-gray-100 flex justify-between items-center">
          <div className="flex gap-2">
            <button 
              type="button"
              onClick={() => setIntent("Perform comprehensive data analysis on quarterly financial spreadsheets and summarize key trends.")}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 cursor-pointer"
            >
              Data Analysis
            </button>
            <button 
              type="button"
              onClick={() => setIntent("Review repository codebase and dependencies for security vulnerabilities and produce an audit report.")}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 cursor-pointer"
            >
              Security Review
            </button>
            <button 
              type="button"
              onClick={() => setIntent("Extract structured entities and key metrics from uploaded PDF documents into JSON.")}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 cursor-pointer"
            >
              Document Processing
            </button>
          </div>
          <Link href={`/app/intent/req-123`}>
            <button className="px-6 py-2 bg-black text-white font-medium rounded-lg hover:bg-gray-800 transition-colors">
              Synthesize Solution
            </button>
          </Link>
        </div>
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 mb-4">Recent Intent Requests</h3>
        <div className="space-y-3">
          <Link href="/app/intent/req-456">
            <div className="p-4 border border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-sm cursor-pointer bg-white flex justify-between items-center">
              <div>
                <h4 className="font-medium text-gray-900">Analyze monthly sales spreadsheets</h4>
                <p className="text-xs text-gray-500 mt-1">Submitted 2 days ago</p>
              </div>
              <span className="px-2.5 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Completed</span>
            </div>
          </Link>
          <Link href="/app/intent/req-789">
            <div className="p-4 border border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-sm cursor-pointer bg-white flex justify-between items-center">
              <div>
                <h4 className="font-medium text-gray-900">Customer Support Escalation routing</h4>
                <p className="text-xs text-gray-500 mt-1">Submitted yesterday</p>
              </div>
              <span className="px-2.5 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded-full">Review Required</span>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}

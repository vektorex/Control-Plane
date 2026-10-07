"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function KnowledgeBase() {
  const [activeTab, setActiveTab] = useState('recently_verified');

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Organizational Knowledge</h1>
          <p className="text-gray-500 mt-2">Shared institutional memory, verified patterns, and decisions.</p>
        </div>
        <div className="flex gap-4">
          <Link href="/app/knowledge/review">
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium">
              Review Queue
            </button>
          </Link>
          <Link href="/app/knowledge/conflicts">
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium">
              Conflicts
            </button>
          </Link>
          <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
            New Knowledge
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {['recently_verified', 'stale', 'project', 'workspace', 'architecture'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab 
                  ? 'border-black text-black' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
            >
              {tab.replace('_', ' ').charAt(0).toUpperCase() + tab.replace('_', ' ').slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Search */}
      <div className="mb-8">
        <input 
          type="text" 
          placeholder="Search organizational knowledge..." 
          className="w-full p-4 rounded-xl border border-gray-200 bg-gray-50 focus:bg-white focus:ring-2 focus:ring-black outline-none"
        />
      </div>

      {/* Content */}
      <div className="space-y-4">
        {[1, 2, 3].map((item) => (
          <div key={item} className="p-6 bg-white border border-gray-200 rounded-xl hover:shadow-sm transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mb-2">
                  Verified
                </span>
                <Link href={`/app/knowledge/item-${item}`}>
                  <h3 className="text-lg font-semibold hover:text-blue-600 cursor-pointer">
                    Database Connection Pooling Strategy
                  </h3>
                </Link>
              </div>
              <span className="text-xs text-gray-500">Updated 2 days ago</span>
            </div>
            <p className="text-gray-600 text-sm mb-4">
              All backend services must use PgBouncer for connection pooling to prevent connection exhaustion. Direct connections to PostgreSQL are prohibited for API endpoints.
            </p>
            <div className="flex gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                Architecture
              </span>
              <span className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                Workspace Scope
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

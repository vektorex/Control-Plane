"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { solutionsService } from '@/services/solutions';

export default function SolutionsDiscovery() {
  const [solutions, setSolutions] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSolutions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await solutionsService.listSolutions();
      setSolutions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn("Could not load solutions:", err);
      setError(err?.message || "Failed to load solutions. Please check your connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSolutions();
  }, [loadSolutions]);

  const filteredSolutions = solutions.filter((sol) => {
    if (activeTab === 'published') return sol.status === 'published' || sol.status === 'active';
    if (activeTab === 'drafts') return sol.status === 'draft' || !sol.status;
    return true;
  });

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
          {[
            { id: 'all', label: 'All Solutions' },
            { id: 'published', label: 'Published' },
            { id: 'drafts', label: 'Drafts' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 text-sm font-medium border-b-2 cursor-pointer transition-colors ${
                activeTab === tab.id
                  ? 'border-black text-black'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {error ? (
        <div className="p-8 border border-red-200 bg-red-50 rounded-xl text-center space-y-3">
          <p className="text-red-600 text-sm">{error}</p>
          <button
            onClick={loadSolutions}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition"
          >
            Retry
          </button>
        </div>
      ) : loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse bg-white border border-gray-200 rounded-xl p-5 space-y-4">
              <div className="flex justify-between items-center">
                <div className="h-4 bg-gray-200 rounded w-16"></div>
                <div className="h-3 bg-gray-100 rounded w-20"></div>
              </div>
              <div className="h-5 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-100 rounded w-full"></div>
              <div className="h-3 bg-gray-100 rounded w-2/3"></div>
              <div className="pt-4 border-t border-gray-100 flex justify-between items-center">
                <div className="h-3 bg-gray-200 rounded w-20"></div>
                <div className="h-3 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          ))}
        </div>
      ) : filteredSolutions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSolutions.map((sol) => (
            <div key={sol.id} className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
              <div className="flex justify-between items-start mb-3">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  sol.status === 'published' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {sol.status || "Draft"}
                </span>
                <span className="text-xs text-gray-500 font-medium">{sol.visibility || "workspace"}</span>
              </div>
              <Link href={`/app/solutions/${sol.id}`}>
                <h3 className="text-lg font-bold hover:text-blue-600 mb-1">{sol.name}</h3>
              </Link>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">{sol.description || sol.objective || "No description provided."}</p>
              <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
                <span>By: {sol.owner_type || "System"}</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-500"></div> Ready</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-12 border-2 border-dashed border-gray-200 rounded-xl text-center space-y-3">
          <div className="w-12 h-12 mx-auto text-gray-400 flex items-center justify-center rounded-full bg-gray-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
          </div>
          <h3 className="text-base font-semibold text-gray-900">No solutions found</h3>
          <p className="text-gray-500 text-sm max-w-sm mx-auto">
            {activeTab === 'all'
              ? 'No solutions exist in this workspace. Create your first solution or use a template.'
              : `No solutions found matching the filter "${activeTab}".`}
          </p>
          <Link href="/app/solutions/new" className="inline-block mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition">
            + Create First Solution
          </Link>
        </div>
      )}
    </div>
  );
}

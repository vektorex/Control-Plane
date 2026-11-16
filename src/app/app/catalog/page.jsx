"use client";

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { catalogService } from '@/services/catalog';

export default function CatalogDiscovery() {
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  const loadItems = useCallback(async (query = '') => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (query.trim()) {
        data = await catalogService.searchItems(query.trim());
      } else {
        data = await catalogService.listCatalogItems();
      }
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn("Could not load catalog items:", err);
      setError(err?.message || "Failed to load service catalog capabilities. Please check your connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadItems(searchQuery);
  };

  const filteredItems = items.filter((item) => {
    if (selectedCategory !== 'all' && item.category) {
      return item.category.toLowerCase().includes(selectedCategory.toLowerCase());
    }
    return true;
  });

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

      <form onSubmit={handleSearchSubmit} className="mb-8 relative">
        <input 
          type="text" 
          placeholder="Search for capabilities (e.g. 'PDF analysis', 'Security review')..." 
          className="w-full p-4 pl-12 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg bg-white"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <svg className="w-6 h-6 text-gray-400 absolute left-4 top-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
      </form>

      <div className="flex gap-8">
        {/* Sidebar Filters */}
        <div className="w-64 flex-shrink-0 space-y-6">
          <div>
            <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-gray-500">Resource Type</h3>
            <div className="space-y-2">
              {[
                { id: 'all', label: 'All Resources' },
                { id: 'workflow', label: 'Workflows' },
                { id: 'team', label: 'Agent Teams' },
                { id: 'agent', label: 'Standalone Agents' },
                { id: 'document', label: 'Document Capabilities' },
              ].map((cat) => (
                <label key={cat.id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    name="category"
                    checked={selectedCategory === cat.id}
                    onChange={() => setSelectedCategory(cat.id)}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span>{cat.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <h3 className="font-semibold mb-3 text-sm uppercase tracking-wider text-gray-500">Categories</h3>
            <div className="space-y-2">
              <Link href="/app/catalog/capabilities">
                <span className="text-sm text-blue-600 hover:underline cursor-pointer">Browse All Categories →</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Catalog Grid */}
        <div className="flex-1">
          {error ? (
            <div className="p-8 border border-red-200 bg-red-50 rounded-xl text-center space-y-3">
              <p className="text-red-600 text-sm">{error}</p>
              <button
                onClick={() => loadItems(searchQuery)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition"
              >
                Retry
              </button>
            </div>
          ) : loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse bg-white border border-gray-200 rounded-xl p-5 space-y-3">
                  <div className="flex justify-between items-center">
                    <div className="h-4 bg-gray-200 rounded w-20"></div>
                    <div className="h-4 bg-gray-100 rounded w-16"></div>
                  </div>
                  <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-100 rounded w-full"></div>
                  <div className="h-3 bg-gray-100 rounded w-2/3"></div>
                  <div className="flex gap-2 pt-2">
                    <div className="h-5 bg-gray-100 rounded w-16"></div>
                    <div className="h-5 bg-gray-100 rounded w-20"></div>
                  </div>
                  <div className="pt-3 border-t border-gray-100 flex justify-between items-center">
                    <div className="h-3 bg-gray-200 rounded w-24"></div>
                    <div className="h-3 bg-gray-200 rounded w-16"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredItems.map((item) => (
                <div key={item.id} className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all">
                  <div className="flex justify-between items-start mb-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                      {item.category || item.item_type || "Capability"}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      {item.status || "Available"}
                    </span>
                  </div>
                  <Link href={`/app/catalog/${item.id}`}>
                    <h3 className="text-lg font-bold hover:text-blue-600 mb-1">{item.name}</h3>
                  </Link>
                  <p className="text-sm text-gray-500 mb-4 line-clamp-2">{item.description || "No description provided."}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {Array.isArray(item.tags) && item.tags.slice(0, 3).map((tag, idx) => (
                      <span key={idx} className="text-xs border border-gray-200 bg-gray-50 px-2 py-1 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
                    <span>By: {item.owner_type || "Platform"}</span>
                    <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-500"></div> Active</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 border-2 border-dashed border-gray-200 rounded-xl text-center space-y-3">
              <div className="w-12 h-12 mx-auto text-gray-400 flex items-center justify-center rounded-full bg-gray-100">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
              </div>
              <h3 className="text-base font-semibold text-gray-900">No capabilities found</h3>
              <p className="text-gray-500 text-sm max-w-sm mx-auto">
                {searchQuery
                  ? `No service catalog items matched "${searchQuery}". Try a different keyword.`
                  : 'No capabilities are registered in the service catalog yet.'}
              </p>
              {searchQuery && (
                <button
                  onClick={() => { setSearchQuery(''); loadItems(''); }}
                  className="mt-2 text-sm text-blue-600 hover:underline"
                >
                  Clear search
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

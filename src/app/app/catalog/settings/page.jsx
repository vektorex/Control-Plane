"use client";

import React from 'react';
import Link from 'next/link';

export default function CatalogSettings() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/catalog" className="text-gray-500 hover:text-gray-700">
          Catalog
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Settings</span>
      </nav>

      <h1 className="text-3xl font-bold mb-8">Catalog Settings</h1>

      <div className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Synchronization</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">Auto-sync capabilities</h4>
                <p className="text-sm text-gray-500">Automatically update catalog items when underlying resources change via Event Bus.</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Freshness Thresholds</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mark as "Aging" after (days)</label>
                <input type="number" className="w-full p-2 border border-gray-300 rounded-md" defaultValue={30} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mark as "Stale" after (days)</label>
                <input type="number" className="w-full p-2 border border-gray-300 rounded-md" defaultValue={90} />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">These settings only apply to metadata freshness. They do not override actual availability status which is checked dynamically.</p>
          </div>
        </div>
        
        <div className="flex justify-end gap-3 mt-8">
          <button className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium">Cancel</button>
          <button className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 font-medium">Save Settings</button>
        </div>
      </div>
    </div>
  );
}

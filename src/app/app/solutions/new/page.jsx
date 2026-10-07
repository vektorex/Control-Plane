"use client";

import React from 'react';
import Link from 'next/link';

export default function CreateSolution() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/solutions" className="text-gray-500 hover:text-gray-700">
          Solutions
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">New Solution</span>
      </nav>

      <h1 className="text-3xl font-bold mb-8">Create AI Work Solution</h1>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Solution Name</label>
            <input type="text" className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g. Automated Threat Intelligence Report" />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Objective</label>
            <textarea className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 h-24" placeholder="Describe what business or technical outcome this solution achieves..."></textarea>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Visibility</label>
            <select className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white">
              <option value="private">Private (Only me)</option>
              <option value="workspace" selected>Workspace (My team)</option>
              <option value="organization">Organization (All workspaces)</option>
            </select>
          </div>

          <div className="pt-4 border-t border-gray-100 flex justify-end gap-3">
            <Link href="/app/solutions">
              <button type="button" className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium">Cancel</button>
            </Link>
            <Link href="/app/solutions/sol-draft-1/builder">
              <button type="button" className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 font-medium">Create & Build</button>
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

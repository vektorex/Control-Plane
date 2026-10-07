"use client";

import React from 'react';
import Link from 'next/link';

export default function KnowledgeDetail({ params }) {
  // params.knowledgeId
  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm">
        <Link href="/app/knowledge" className="text-gray-500 hover:text-gray-700">
          Organizational Knowledge
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Database Connection Pooling Strategy</span>
      </nav>

      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Verified
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Fresh
            </span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Database Connection Pooling Strategy</h1>
          <p className="text-gray-500">Last verified 2 days ago by Admin User</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium">
            Edit
          </button>
          <button className="px-4 py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 text-sm font-medium">
            Report Conflict
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="col-span-2 space-y-8">
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-xl font-semibold mb-4">Summary</h2>
            <p className="text-gray-700 leading-relaxed mb-6">
              All backend services must use PgBouncer for connection pooling to prevent connection exhaustion. Direct connections to PostgreSQL are prohibited for API endpoints.
            </p>
            
            <h2 className="text-xl font-semibold mb-4">Content</h2>
            <div className="prose prose-sm text-gray-700">
              <p>During the incident on Oct 1st, we experienced connection exhaustion due to rapid scaling of the API instances. Each instance was establishing direct connections to the DB.</p>
              <p><strong>Decision:</strong></p>
              <ul>
                <li>Implement PgBouncer in transaction mode.</li>
                <li>Set max API instance connections to 5.</li>
                <li>Require application-level timeout configurations.</li>
              </ul>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">Evidence & Sources</h2>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="mt-1">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <div>
                  <h4 className="font-medium text-sm">Post-mortem: DB Exhaustion Incident</h4>
                  <p className="text-xs text-gray-500 mt-1">Source: Security Incident • Verified Evidence</p>
                </div>
              </li>
            </ul>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="font-semibold mb-4">Metadata</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Knowledge Type</dt>
                <dd className="font-medium">Architecture Decision</dd>
              </div>
              <div>
                <dt className="text-gray-500">Scope</dt>
                <dd className="font-medium">Workspace</dd>
              </div>
              <div>
                <dt className="text-gray-500">Classification</dt>
                <dd className="font-medium">Internal</dd>
              </div>
              <div>
                <dt className="text-gray-500">Current Version</dt>
                <dd className="font-medium">v3</dd>
              </div>
            </dl>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="font-semibold mb-4">Impact</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Referenced By</dt>
                <dd className="font-medium">12 Workflows</dd>
              </div>
              <div>
                <dt className="text-gray-500">Used By</dt>
                <dd className="font-medium">3 Agents</dd>
              </div>
            </dl>
            <button className="mt-4 w-full px-4 py-2 text-sm text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg font-medium transition-colors">
              View Graph
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

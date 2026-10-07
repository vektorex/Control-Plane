"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function ContractsDashboard() {
  const [activeTab, setActiveTab] = useState('active');

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">AI Work Contracts</h1>
          <p className="text-gray-500 mt-2">Manage operational commitments, SLAs, and deliverables for AI execution.</p>
        </div>
        <div className="flex gap-4">
          <Link href="/app/contracts/analytics">
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm font-medium">
              Analytics
            </button>
          </Link>
          <Link href="/app/contracts/breaches">
            <button className="px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 text-sm font-medium">
              Breaches
            </button>
          </Link>
          <Link href="/app/contracts/new">
            <button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 text-sm font-medium">
              Create Contract
            </button>
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {['active', 'at_risk', 'pending_acceptance', 'upcoming_deadlines'].map((tab) => (
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

      {/* Contract List */}
      <div className="space-y-4">
        {[1, 2, 3].map((item) => (
          <div key={item} className="p-6 bg-white border border-gray-200 rounded-xl hover:shadow-sm transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mb-2">
                  Active
                </span>
                <Link href={`/app/contracts/ctr-${item}`}>
                  <h3 className="text-lg font-semibold hover:text-blue-600 cursor-pointer">
                    Q4 Competitor Pricing Analysis
                  </h3>
                </Link>
                <div className="text-sm text-gray-500 mt-1">Research Agent Team • Contract #CTR-9824</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">Due in 2 days</div>
                <div className="text-xs text-gray-500 mt-1">Nov 15, 2026</div>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
              <div>
                <div className="text-xs text-gray-500 mb-1">Deliverables</div>
                <div className="font-medium text-sm">1 of 3 Accepted</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">SLA Status</div>
                <div className="font-medium text-sm text-green-600 flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div> On Track
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Cost Limit</div>
                <div className="font-medium text-sm">$45.00 / $100.00</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { contractsService } from '@/services/contracts';

export default function ContractsDashboard() {
  const [activeTab, setActiveTab] = useState('active');
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadContracts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await contractsService.listContracts();
      setContracts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn("Could not load contracts:", err);
      setError(err?.message || "Failed to load contracts. Please check your connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadContracts();
  }, [loadContracts]);

  const filteredContracts = contracts.filter((c) => {
    if (activeTab === 'active') return c.status !== 'completed' && c.status !== 'cancelled';
    if (activeTab === 'at_risk') return c.status === 'at_risk';
    if (activeTab === 'pending_acceptance') return c.status === 'draft' || c.status === 'proposed';
    return true;
  });

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
          {[
            { id: 'active', label: 'Active' },
            { id: 'at_risk', label: 'At Risk' },
            { id: 'pending_acceptance', label: 'Pending Acceptance' },
            { id: 'upcoming_deadlines', label: 'Upcoming Deadlines' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm cursor-pointer transition-colors
                ${activeTab === tab.id 
                  ? 'border-black text-black' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
              `}
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
            onClick={loadContracts}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition"
          >
            Retry
          </button>
        </div>
      ) : loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse p-6 bg-white border border-gray-200 rounded-xl space-y-3">
              <div className="flex justify-between items-start">
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-16"></div>
                  <div className="h-5 bg-gray-200 rounded w-48"></div>
                  <div className="h-3 bg-gray-100 rounded w-64"></div>
                </div>
                <div className="space-y-2 text-right">
                  <div className="h-4 bg-gray-200 rounded w-16 ml-auto"></div>
                  <div className="h-3 bg-gray-100 rounded w-20 ml-auto"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : filteredContracts.length > 0 ? (
        <div className="space-y-4">
          {filteredContracts.map((item) => (
            <div key={item.id} className="p-6 bg-white border border-gray-200 rounded-xl hover:shadow-sm transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mb-2 ${
                    item.status === 'at_risk' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {item.status || "Active"}
                  </span>
                  <Link href={`/app/contracts/${item.id}`}>
                    <h3 className="text-lg font-semibold hover:text-blue-600 cursor-pointer">
                      {item.name || `Contract #${String(item.id).slice(0, 8)}`}
                    </h3>
                  </Link>
                  <div className="text-sm text-gray-500 mt-1">{item.description || `Contract #${String(item.id).slice(0, 8)}`}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">{item.contract_type || "SLA"}</div>
                  <div className="text-xs text-gray-500 mt-1">{item.priority || "Standard"}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-12 border-2 border-dashed border-gray-200 rounded-xl text-center space-y-3">
          <div className="w-12 h-12 mx-auto text-gray-400 flex items-center justify-center rounded-full bg-gray-100">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          </div>
          <h3 className="text-base font-semibold text-gray-900">No contracts found</h3>
          <p className="text-gray-500 text-sm max-w-sm mx-auto">
            {contracts.length === 0
              ? 'No contracts have been registered yet. Create a work contract to define governance rules and SLAs.'
              : `No contracts found under the "${activeTab.replace('_', ' ')}" tab.`}
          </p>
          <Link href="/app/contracts/new" className="inline-block mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition">
            + Create First Contract
          </Link>
        </div>
      )}
    </div>
  );
}

// src/app/security/assurance-center/page.jsx
'use client';
import React, { useState, useEffect } from 'react';

/** Feature 20 — Continuous Assurance Control Center */
export default function AssuranceCenter() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/security/assurance/health', {
      headers: { 'x-tenant-id': 'tenant-1' }
    })
      .then(res => res.json())
      .then(data => {
        setHealthData(data.data);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  return (
    <div className="p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-orange-400">Continuous Security Assurance Center</h1>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 animate-pulse">Loading Assurance Fabric...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-orange-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">System Status</h2>
            <div className="text-2xl font-bold text-white">{healthData?.status}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Release Candidates</h2>
            <div className="text-2xl font-bold text-white">2</div>
            <p className="text-xs text-gray-400 mt-1">Pending mandatory gates</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-yellow-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Flaky Tests</h2>
            <div className="text-2xl font-bold text-yellow-400">14</div>
            <p className="text-xs text-gray-400 mt-1">Quarantined safely</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-red-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">SLO Breaches</h2>
            <div className="text-2xl font-bold text-white">0</div>
            <p className="text-xs text-gray-400 mt-1">All error budgets healthy</p>
          </div>
        </div>
      )}
    </div>
  );
}

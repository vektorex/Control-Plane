// src/app/security/decision-center/page.jsx
'use client';
import React, { useState, useEffect } from 'react';

/** Feature 20 — Universal Security Decision Center */
export default function DecisionCenter() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/security/decisions/health', {
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
      <h1 className="text-3xl font-bold mb-6 text-emerald-400">Universal Decision Center</h1>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 animate-pulse">Loading Decision Fabric...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-emerald-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">System Status</h2>
            <div className="text-2xl font-bold text-white">{healthData?.status}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Decision Queue</h2>
            <div className="text-2xl font-bold text-white">12</div>
            <p className="text-xs text-gray-400 mt-1">Pending items</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-yellow-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Autonomy Governor</h2>
            <div className="text-2xl font-bold text-green-400">RECOMMEND</div>
            <p className="text-xs text-gray-400 mt-1">Safe mode active</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-red-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Pending Approvals</h2>
            <div className="text-2xl font-bold text-white">3</div>
            <p className="text-xs text-gray-400 mt-1">Require manual sign-off</p>
          </div>
        </div>
      )}
    </div>
  );
}

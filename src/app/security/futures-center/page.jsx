// src/app/security/futures-center/page.jsx
'use client';
import React, { useState, useEffect } from 'react';

/** Feature 19 & 21 — Cyber Futures Command Center & Scenario Comparison */
export default function FuturesCenter() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/security/futures/health', {
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
      <h1 className="text-3xl font-bold mb-6 text-indigo-400">Cyber Futures & Strategy Center</h1>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 animate-pulse">Loading Simulation Data...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-indigo-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">System Status</h2>
            <div className="text-2xl font-bold text-white">{healthData?.status}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Active Scenarios</h2>
            <div className="text-2xl font-bold text-white">4</div>
            <p className="text-xs text-gray-400 mt-1">Simulating in background</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-purple-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Digital Twins</h2>
            <div className="text-2xl font-bold text-green-400">SYNCED</div>
            <p className="text-xs text-gray-400 mt-1">Snapshot v4.0.1</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-orange-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Simulations</h2>
            <div className="text-2xl font-bold text-white">ISOLATED</div>
            <p className="text-xs text-gray-400 mt-1">Non-destructive execution only</p>
          </div>
        </div>
      )}
    </div>
  );
}

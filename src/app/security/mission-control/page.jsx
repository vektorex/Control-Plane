// src/app/security/mission-control/page.jsx
'use client';
import React, { useState, useEffect } from 'react';

/** Feature 20 — Autonomous Security Mission Control Center */
export default function MissionControlCenter() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/security/missions/health', {
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
      <h1 className="text-3xl font-bold mb-6 text-pink-400">Mission Control & Agent Orchestration</h1>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 animate-pulse">Loading Mission State...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-pink-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Platform Status</h2>
            <div className="text-2xl font-bold text-white">{healthData?.status}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Active Missions</h2>
            <div className="text-2xl font-bold text-white">5</div>
            <p className="text-xs text-gray-400 mt-1">Executing within budget limits</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-yellow-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Agent Fleet</h2>
            <div className="text-2xl font-bold text-green-400">14 ONLINE</div>
            <p className="text-xs text-gray-400 mt-1">Delegation boundary enforced</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-red-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Security Council</h2>
            <div className="text-2xl font-bold text-white">1</div>
            <p className="text-xs text-gray-400 mt-1">Mission awaiting manual review</p>
          </div>
        </div>
      )}
    </div>
  );
}

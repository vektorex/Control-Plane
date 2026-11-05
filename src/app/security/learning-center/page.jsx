// src/app/security/learning-center/page.jsx
'use client';
import React, { useState, useEffect } from 'react';

/**
 * Feature 20 - Learning Operations & Governance Center
 */
export default function LearningCenter() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/security/learning/health', {
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
      <h1 className="text-3xl font-bold mb-6 text-green-400">Learning Operations & Governance Center</h1>
      
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 animate-pulse">Loading Platform State...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-green-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">System Status</h2>
            <div className="text-2xl font-bold text-white">{healthData?.status}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Active Services</h2>
            <ul className="text-sm text-gray-400 mt-2 list-disc pl-4">
              {healthData?.services.map(s => <li key={s}>{s}</li>)}
            </ul>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-purple-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Adversarial Defense</h2>
            <div className="text-2xl font-bold text-white">ACTIVE</div>
            <p className="text-xs text-gray-400 mt-1">Poisoning protection enabled</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-yellow-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Promotion Gate</h2>
            <div className="text-2xl font-bold text-white">ENFORCED</div>
            <p className="text-xs text-gray-400 mt-1">Approval limits active</p>
          </div>
        </div>
      )}
    </div>
  );
}

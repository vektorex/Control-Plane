// src/app/security/immunity-center/page.jsx
'use client';
import React, { useState, useEffect } from 'react';

/**
 * Digital Immunity Center (Feature 21)
 */
export default function ImmunityCenter() {
  const [immunityData, setImmunityData] = useState(null);

  useEffect(() => {
    fetch('/api/security/immunity?action=model', {
      headers: { 'x-tenant-id': 'tenant-1' }
    })
      .then(res => res.json())
      .then(data => setImmunityData(data.data))
      .catch(console.error);
  }, []);

  return (
    <div className="p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-blue-400">Digital Immunity Center</h1>
      
      {immunityData ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Immunity Score</h2>
            <div className="text-5xl font-bold text-white">{Math.round(immunityData.immunityScore)}/100</div>
            <p className="mt-2 text-sm text-gray-400">Confidence: {(immunityData.confidence * 100).toFixed(0)}%</p>
          </div>

          <div className={`bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 ${immunityData.healthState === 'HEALTHY' ? 'border-green-500' : 'border-yellow-500'}`}>
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Health State</h2>
            <div className="text-3xl font-bold">{immunityData.healthState}</div>
            <p className="mt-2 text-sm text-gray-400">Trend: {immunityData.trend}</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg shadow-lg border-l-4 border-red-500">
            <h2 className="text-xl font-semibold mb-2 text-gray-300">Critical Weaknesses</h2>
            <ul className="list-disc pl-5 mt-2 space-y-1 text-gray-200">
              {immunityData.criticalWeaknesses.map(w => (
                <li key={w} className="capitalize">{w}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-400 animate-pulse">Loading Immunity Telemetry...</p>
        </div>
      )}
    </div>
  );
}

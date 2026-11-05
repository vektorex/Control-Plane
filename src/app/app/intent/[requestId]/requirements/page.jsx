"use client";

import React, { useState } from 'react';
import Link from 'next/link';

export default function IntentRequirements({ params }) {
  // params.requestId
  const [explicitReqs, setExplicitReqs] = useState([
    { id: 1, type: "Capability", desc: "Security Vulnerability Scanning", required: "Yes" },
    { id: 2, type: "Output", desc: "Verified Security Report", required: "Yes" },
  ]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newType, setNewType] = useState("Capability");
  const [newDesc, setNewDesc] = useState("");

  const handleAddRequirement = (e) => {
    e.preventDefault();
    if (!newDesc.trim()) return;
    setExplicitReqs((prev) => [
      ...prev,
      { id: Date.now(), type: newType, desc: newDesc, required: "Yes" }
    ]);
    setNewDesc("");
    setShowAddModal(false);
  };

  const handleRemove = (id) => {
    setExplicitReqs((prev) => prev.filter((r) => r.id !== id));
  };
  
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/intent" className="text-gray-500 hover:text-gray-700">
          Intent Workspace
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <Link href={`/app/intent/${params.requestId}`} className="text-gray-500 hover:text-gray-700">
          Request #{params.requestId}
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Requirements</span>
      </nav>

      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold">Extracted Requirements</h1>
          <p className="text-gray-500 mt-2">These requirements will drive the Service Catalog capability discovery.</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 border border-gray-300 bg-white rounded-lg text-sm font-medium hover:bg-gray-50 cursor-pointer"
          >
            + Add Requirement
          </button>
        </div>
      </div>

      <div className="space-y-6">
        
        {/* Explicit Requirements */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wider">Explicit (From User Intent)</h3>
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-4 font-medium text-gray-700 w-32">Type</th>
                  <th className="p-4 font-medium text-gray-700">Description</th>
                  <th className="p-4 font-medium text-gray-700 w-24">Required</th>
                  <th className="p-4 font-medium text-gray-700 w-24">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {explicitReqs.map((req) => (
                  <tr key={req.id}>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs border ${
                        req.type === 'Capability' ? 'bg-blue-50 text-blue-700 border-blue-100' : 'bg-purple-50 text-purple-700 border-purple-100'
                      }`}>
                        {req.type}
                      </span>
                    </td>
                    <td className="p-4 font-medium">{req.desc}</td>
                    <td className="p-4"><span className="text-green-600 font-medium">{req.required}</span></td>
                    <td className="p-4">
                      <button 
                        onClick={() => handleRemove(req.id)}
                        className="text-red-500 hover:text-red-700 text-xs font-medium cursor-pointer"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Policy Requirements */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wider flex items-center gap-2">
            Policy Applied
            <span className="text-xs font-normal normal-case text-gray-500 bg-gray-100 px-2 py-0.5 rounded">Non-removable</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm text-left">
              <tbody className="divide-y divide-gray-200">
                <tr>
                  <td className="p-4 w-32"><span className="px-2 py-1 bg-red-50 text-red-700 rounded text-xs border border-red-100">Governance</span></td>
                  <td className="p-4 font-medium">External API calls require Data Steward Approval</td>
                  <td className="p-4 text-xs text-gray-500 italic">Source: Workspace Security Policy</td>
                </tr>
                <tr>
                  <td className="p-4 w-32"><span className="px-2 py-1 bg-red-50 text-red-700 rounded text-xs border border-red-100">Evaluation</span></td>
                  <td className="p-4 font-medium">Security findings must include citation links</td>
                  <td className="p-4 text-xs text-gray-500 italic">Source: Code Quality Standards</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <div className="mt-8 pt-6 border-t border-gray-200 flex justify-end gap-3">
        <Link href={`/app/intent/${params.requestId}/candidates`}>
          <button className="px-6 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800 cursor-pointer">
            Confirm & Generate Candidates →
          </button>
        </Link>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleAddRequirement} className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Add Requirement</h3>
              <button 
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-gray-600 text-lg cursor-pointer"
              >
                ✕
              </button>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Requirement Type</label>
              <select 
                value={newType} 
                onChange={(e) => setNewType(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="Capability">Capability</option>
                <option value="Output">Output</option>
                <option value="Constraint">Constraint</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
              <input 
                type="text" 
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="E.g. Static code linting with 0 errors"
                className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                required
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button 
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium cursor-pointer"
              >
                Cancel
              </button>
              <button 
                type="submit"
                className="px-4 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800 cursor-pointer"
              >
                Add
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}

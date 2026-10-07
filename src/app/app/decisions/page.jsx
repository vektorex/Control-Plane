"use client";

import React from 'react';
import Link from 'next/link';

export default function DecisionCenter() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Decision Intelligence Center</h1>
        <p className="text-gray-500 mt-2">Observe readiness, investigate execution blockers, and review evidence-backed system decisions.</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-xl border border-gray-200">
          <span className="text-xs text-gray-500 uppercase font-semibold">Active Blockers</span>
          <div className="text-3xl font-bold text-red-600 mt-1">12</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200">
          <span className="text-xs text-gray-500 uppercase font-semibold">Conditionally Ready</span>
          <div className="text-3xl font-bold text-amber-600 mt-1">5</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200">
          <span className="text-xs text-gray-500 uppercase font-semibold">Execution Ready</span>
          <div className="text-3xl font-bold text-green-600 mt-1">48</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-gray-200">
          <span className="text-xs text-gray-500 uppercase font-semibold">Stale Evidence</span>
          <div className="text-3xl font-bold text-gray-900 mt-1">3</div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 className="font-semibold text-gray-900">Recent Decisions</h2>
          <div className="flex gap-2">
            <select className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white text-gray-700">
              <option>All States</option>
              <option>Blocked</option>
              <option>Ready</option>
            </select>
            <select className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white text-gray-700">
              <option>All Subject Types</option>
              <option>Solution Execution</option>
              <option>Agent Deployment</option>
            </select>
          </div>
        </div>
        
        <table className="w-full text-sm text-left">
          <thead className="bg-white border-b border-gray-200">
            <tr>
              <th className="p-4 font-semibold text-gray-900">Subject</th>
              <th className="p-4 font-semibold text-gray-900">Decision Type</th>
              <th className="p-4 font-semibold text-gray-900">State</th>
              <th className="p-4 font-semibold text-gray-900">Time</th>
              <th className="p-4 font-semibold text-gray-900 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            
            <tr className="hover:bg-gray-50">
              <td className="p-4">
                <div className="font-medium text-gray-900">Customer Contract Analyzer</div>
                <div className="text-xs text-gray-500">Solution Execution</div>
              </td>
              <td className="p-4">Execution Readiness</td>
              <td className="p-4">
                <span className="px-2.5 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full flex w-fit items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-600"></div> Blocked
                </span>
              </td>
              <td className="p-4 text-gray-500">2 mins ago</td>
              <td className="p-4 text-right">
                <Link href="/app/decisions/dec-123">
                  <button className="text-blue-600 hover:underline font-medium">Investigate</button>
                </Link>
              </td>
            </tr>

            <tr className="hover:bg-gray-50">
              <td className="p-4">
                <div className="font-medium text-gray-900">SAST Review Agent</div>
                <div className="text-xs text-gray-500">Agent Configuration</div>
              </td>
              <td className="p-4">Execution Readiness</td>
              <td className="p-4">
                <span className="px-2.5 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded-full flex w-fit items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-600"></div> Conditionally Ready
                </span>
              </td>
              <td className="p-4 text-gray-500">1 hour ago</td>
              <td className="p-4 text-right">
                <Link href="/app/decisions/dec-456">
                  <button className="text-blue-600 hover:underline font-medium">Investigate</button>
                </Link>
              </td>
            </tr>

          </tbody>
        </table>
      </div>
    </div>
  );
}

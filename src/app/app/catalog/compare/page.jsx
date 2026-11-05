"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function CatalogCompare() {
  const router = useRouter();
  const [items, setItems] = useState([
    {
      id: "alpha",
      type: "Agent Team",
      typeColor: "bg-purple-100 text-purple-800",
      title: "Deep Research Team Alpha",
      category: "Research & Analysis",
      modalities: ["Text", "Data"],
      approvals: "None",
      approvalsClass: "text-gray-500",
      available: true
    },
    {
      id: "extraction",
      type: "Workflow",
      typeColor: "bg-blue-100 text-blue-800",
      title: "Customer Onboarding Extraction",
      category: "Data & Operations",
      modalities: ["Text", "Image (OCR)"],
      approvals: "Data Steward Approval (Confidential)",
      approvalsClass: "text-amber-600 font-medium",
      available: true
    }
  ]);

  const removeItem = (id) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/catalog" className="text-gray-500 hover:text-gray-700">
          Catalog
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Compare</span>
      </nav>

      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold">Compare Capabilities</h1>
          <p className="text-gray-500 mt-2">Factually compare up to 4 catalog items side-by-side.</p>
        </div>
        <button 
          type="button"
          onClick={() => router.push('/app/catalog')}
          className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-sm hover:bg-gray-50 cursor-pointer"
        >
          + Add Item
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr>
              <th className="p-4 border-b border-gray-200 bg-gray-50 w-64">Attribute</th>
              {items.map(item => (
                <th key={item.id} className="p-4 border-b border-gray-200 w-1/2">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mb-2 ${item.typeColor}`}>
                        {item.type}
                      </span>
                      <h3 className="font-bold text-lg">{item.title}</h3>
                    </div>
                    <button 
                      type="button"
                      onClick={() => removeItem(item.id)}
                      className="text-gray-400 hover:text-gray-600 p-1 cursor-pointer"
                      title="Remove from comparison"
                    >
                      ✕
                    </button>
                  </div>
                </th>
              ))}
              {items.length === 0 && (
                <th className="p-4 border-b border-gray-200 text-gray-400 font-normal">
                  No items selected to compare. Click "+ Add Item" to add capabilities.
                </th>
              )}
            </tr>
          </thead>
          {items.length > 0 && (
            <tbody className="text-sm">
              <tr>
                <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Category</td>
                {items.map(item => (
                  <td key={item.id} className="p-4 border-b border-gray-200">{item.category}</td>
                ))}
              </tr>
              <tr>
                <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Supported Modalities</td>
                {items.map(item => (
                  <td key={item.id} className="p-4 border-b border-gray-200">
                    <div className="flex gap-2">
                      {item.modalities.map(m => (
                        <span key={m} className="px-2 py-1 bg-gray-100 rounded text-xs">{m}</span>
                      ))}
                    </div>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Required Approvals</td>
                {items.map(item => (
                  <td key={item.id} className={`p-4 border-b border-gray-200 ${item.approvalsClass}`}>
                    {item.approvals}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-4 border-b border-gray-200 font-medium text-gray-700 bg-gray-50">Availability</td>
                {items.map(item => (
                  <td key={item.id} className="p-4 border-b border-gray-200">
                    <span className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                      Available
                    </span>
                  </td>
                ))}
              </tr>
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}

"use client";

import React from 'react';
import Link from 'next/link';

export default function CatalogCapabilities() {
  const categories = [
    { name: 'Research', count: 12 },
    { name: 'Analysis', count: 8 },
    { name: 'Coding', count: 5 },
    { name: 'Documents', count: 24 },
    { name: 'Knowledge', count: 6 },
    { name: 'Automation', count: 15 },
    { name: 'Security', count: 3 },
    { name: 'Planning', count: 2 },
    { name: 'Data', count: 18 },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <nav className="mb-6 text-sm">
        <Link href="/app/catalog" className="text-gray-500 hover:text-gray-700">
          Catalog
        </Link>
        <span className="mx-2 text-gray-400">/</span>
        <span className="text-gray-900">Capabilities</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold">Capability Explorer</h1>
        <p className="text-gray-500 mt-2">Browse the catalog by functional domains and capability areas.</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {categories.map(cat => (
          <Link key={cat.name} href={`/app/catalog?category=${cat.name.toLowerCase()}`}>
            <div className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer flex justify-between items-center">
              <h3 className="text-lg font-semibold">{cat.name}</h3>
              <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm font-medium">{cat.count}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

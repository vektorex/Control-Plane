import React from 'react';
import Link from 'next/link';

export default function ReleaseOptimizationDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Release Optimization</h1>
                    <p className="text-gray-400 mt-2">Scenario analysis, bottleneck detection, and cross-release optimization.</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/app/release-optimization/scenarios/new" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        New Scenario
                    </Link>
                </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Link href="/app/release-optimization/scenarios" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">Active Scenarios</h2>
                    <p className="text-2xl font-bold text-blue-400 mt-2">3 Analyzing</p>
                </Link>
                <Link href="/app/release-coordination/trains" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-purple-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">Coordination Base</h2>
                    <p className="text-2xl font-bold text-purple-400 mt-2">View Trains</p>
                </Link>
                <div className="block p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Bottlenecks</h2>
                    <p className="text-2xl font-bold text-red-400 mt-2">1 Blocking</p>
                </div>
            </div>
        </div>
    );
}
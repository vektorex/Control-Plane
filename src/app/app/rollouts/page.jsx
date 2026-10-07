import React from 'react';
import Link from 'next/link';
import RolloutCard from '@/components/rollouts/RolloutCard';

export default function RolloutsDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Progressive Delivery</h1>
                    <p className="text-gray-400 mt-2">Gradually expose, observe, and control releases in production.</p>
                </div>
                <Link href="/app/rollouts/new" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    Create Rollout
                </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Link href="/app/rollouts/history" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">History</h2>
                </Link>
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Active</h2>
                    <p className="text-2xl font-bold text-blue-400 mt-2">2</p>
                </div>
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Paused</h2>
                    <p className="text-2xl font-bold text-yellow-400 mt-2">1</p>
                </div>
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Failed</h2>
                    <p className="text-2xl font-bold text-red-400 mt-2">0</p>
                </div>
            </div>
            
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Active Rollouts</h2>
                <div className="space-y-4">
                    <RolloutCard status="running" name="Canary: Q4 Security Rules" stage="25% Traffic" />
                    <RolloutCard status="paused" name="Cohort: Premium Users Alpha" stage="Evaluation Gate Failed" />
                </div>
            </div>
        </div>
    );
}
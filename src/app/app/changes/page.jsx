import React from 'react';
import Link from 'next/link';
import ChangeCard from '@/components/changes/ChangeCard';

export default function ChangeDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Change Intelligence & Impact Analysis</h1>
                    <p className="text-gray-400 mt-2">Analyze what will break before you make a change.</p>
                </div>
                <Link href="/app/changes/new" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    Propose Change
                </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Link href="/app/changes/history" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-purple-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Change History</h2>
                    <p className="text-gray-400">Immutable audit log of past changes and their impact.</p>
                </Link>
                <Link href="/app/changes/settings" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Settings & Policies</h2>
                    <p className="text-gray-400">Configure how changes are analyzed and scoped.</p>
                </Link>
            </div>
            
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Pending Analysis</h2>
                <div className="space-y-4">
                    <ChangeCard status="analyzing" />
                </div>
            </div>
        </div>
    );
}
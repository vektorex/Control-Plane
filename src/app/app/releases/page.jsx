import React from 'react';
import Link from 'next/link';
import ReleaseCard from '@/components/releases/ReleaseCard';

export default function ReleasesDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Release & Deployment</h1>
                    <p className="text-gray-400 mt-2">Govern, Stage, Promote, and Observe AI Work changes.</p>
                </div>
                <Link href="/app/releases/new" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    Create Release
                </Link>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Link href="/app/releases/history" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-purple-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">History & Audit</h2>
                    <p className="text-gray-400">Immutable deployment history.</p>
                </Link>
                <Link href="/app/releases/environments" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-green-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Environments</h2>
                    <p className="text-gray-400">Manage staging & production readiness policies.</p>
                </Link>
                <Link href="/app/releases/settings" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Policies & Freezes</h2>
                    <p className="text-gray-400">Configure global release policies and freezes.</p>
                </Link>
            </div>
            
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Active Releases</h2>
                <div className="space-y-4">
                    <ReleaseCard status="Validation Required" name="Update Data Classifier Agent" />
                    <ReleaseCard status="In Progress" name="Promote Q4 Workflows" />
                </div>
            </div>
        </div>
    );
}
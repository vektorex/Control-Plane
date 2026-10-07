import React from 'react';
import Link from 'next/link';

export default function DecisionsDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">Decision Intelligence & Readiness</h1>
            <p className="text-gray-400 mb-8">Analyze execution readiness, view blockers, and trace decision provenance.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Link href="/app/decisions/readiness" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Readiness Assessments</h2>
                    <p className="text-gray-400">Evaluate whether solutions, workflows, or agents are ready to execute.</p>
                </Link>
                
                <Link href="/app/decisions/blockers" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-red-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Active Blockers</h2>
                    <p className="text-gray-400">View and resolve constraints preventing execution across the platform.</p>
                </Link>
                
                <Link href="/app/decisions/evidence" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-green-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Evidence & Provenance</h2>
                    <p className="text-gray-400">Inspect the factual basis for automated decisions and readiness states.</p>
                </Link>
                
                <Link href="/app/decisions/history" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-purple-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Decision History</h2>
                    <p className="text-gray-400">Immutable audit log of past decisions and state changes.</p>
                </Link>
                
                <Link href="/app/decisions/settings" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-500 transition-colors">
                    <h2 className="text-xl font-semibold text-white mb-2">Decision Policies</h2>
                    <p className="text-gray-400">Configure how decisions evaluate evidence and constraints.</p>
                </Link>
            </div>
        </div>
    );
}
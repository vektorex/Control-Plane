"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import ChangeCard from '@/components/changes/ChangeCard';
import { changesService } from '@/services/changes';

export default function ChangeDashboard() {
    const [changes, setChanges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadChanges = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await changesService.listChangeRequests();
            setChanges(Array.isArray(data) ? data : []);
        } catch (err) {
            console.warn("Could not load change requests:", err);
            setError(err?.message || "Failed to load change requests. Please check your connection.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadChanges();
    }, [loadChanges]);

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
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700">
                    <h2 className="text-xl font-semibold text-white mb-2">Pending Impact Audits</h2>
                    <p className="text-2xl font-bold text-yellow-400 mt-2">
                        {loading ? "..." : changes.filter(c => c.status === 'analyzing' || c.status === 'pending').length}
                    </p>
                </div>
            </div>
            
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Pending & Active Changes</h2>
                {error ? (
                    <div className="p-6 bg-red-900/20 border border-red-800 rounded-xl text-center space-y-3">
                        <p className="text-red-400 text-sm">{error}</p>
                        <button 
                            onClick={loadChanges} 
                            className="px-4 py-1.5 bg-red-800 hover:bg-red-700 text-white text-sm rounded-lg transition"
                        >
                            Retry
                        </button>
                    </div>
                ) : loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="animate-pulse bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-center">
                                <div className="space-y-2">
                                    <div className="h-4 bg-gray-700 rounded w-48"></div>
                                    <div className="h-3 bg-gray-700/60 rounded w-64"></div>
                                </div>
                                <div className="h-6 bg-gray-700 rounded w-20"></div>
                            </div>
                        ))}
                    </div>
                ) : changes.length > 0 ? (
                    <div className="space-y-4">
                        {changes.map((chg) => (
                            <Link key={chg.id} href={`/app/changes/${chg.id}`}>
                                <ChangeCard
                                    title={chg.title || `Change ${chg.id.slice(0, 8)}`}
                                    description={chg.description || `${chg.change_type || "Update"} on ${chg.subject_type || "Agent"}`}
                                    status={chg.status || "draft"}
                                />
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="p-8 bg-gray-850 border border-gray-800 rounded-xl text-center space-y-3">
                        <div className="w-12 h-12 mx-auto text-gray-500 flex items-center justify-center rounded-full bg-gray-800">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                        </div>
                        <h3 className="text-lg font-medium text-white">No active change requests pending analysis</h3>
                        <p className="text-gray-400 text-sm max-w-md mx-auto">Submit a change request to run impact analysis, check dependencies, and verify simulation safety.</p>
                        <Link href="/app/changes/new" className="inline-block mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition">
                            + Propose New Change
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}

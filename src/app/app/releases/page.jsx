"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import ReleaseCard from '@/components/releases/ReleaseCard';
import { releasesService } from '@/services/releases';

export default function ReleasesDashboard() {
    const [releases, setReleases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadReleases = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await releasesService.listReleases();
            setReleases(Array.isArray(data) ? data : []);
        } catch (err) {
            console.warn("Could not fetch releases:", err);
            setError(err?.message || "Failed to load releases. Please check your connection.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadReleases();
    }, [loadReleases]);

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
                {error ? (
                    <div className="p-6 bg-red-900/20 border border-red-800 rounded-xl text-center space-y-3">
                        <p className="text-red-400 text-sm">{error}</p>
                        <button 
                            onClick={loadReleases} 
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
                                    <div className="h-3 bg-gray-700/60 rounded w-32"></div>
                                </div>
                                <div className="h-6 bg-gray-700 rounded w-20"></div>
                            </div>
                        ))}
                    </div>
                ) : releases.length > 0 ? (
                    <div className="space-y-4">
                        {releases.map((rel) => (
                            <Link key={rel.id} href={`/app/releases/${rel.id}`}>
                                <ReleaseCard status={rel.status || "draft"} name={rel.name} />
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="p-8 bg-gray-850 border border-gray-800 rounded-xl text-center space-y-3">
                        <div className="w-12 h-12 mx-auto text-gray-500 flex items-center justify-center rounded-full bg-gray-800">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
                        </div>
                        <h3 className="text-lg font-medium text-white">No active releases</h3>
                        <p className="text-gray-400 text-sm max-w-md mx-auto">No release candidates have been created for this workspace yet. Create a release to govern and stage changes.</p>
                        <Link href="/app/releases/new" className="inline-block mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition">
                            + Create First Release
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}

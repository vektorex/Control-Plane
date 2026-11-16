"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import RolloutCard from '@/components/rollouts/RolloutCard';
import { rolloutsService } from '@/services/rollouts';

export default function RolloutsDashboard() {
    const [rollouts, setRollouts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadRollouts = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await rolloutsService.listRollouts();
            setRollouts(Array.isArray(data) ? data : []);
        } catch (err) {
            console.warn("Could not load rollouts:", err);
            setError(err?.message || "Failed to load progressive rollouts. Please check your connection.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadRollouts();
    }, [loadRollouts]);

    const activeCount = rollouts.filter(r => r.status === 'running' || r.status === 'in_progress').length;
    const pausedCount = rollouts.filter(r => r.status === 'paused').length;
    const failedCount = rollouts.filter(r => r.status === 'aborted' || r.status === 'failed').length;

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
                    <p className="text-xs text-gray-400 mt-2">View past delivery audits</p>
                </Link>
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Active</h2>
                    <p className="text-2xl font-bold text-blue-400 mt-2">{loading ? "..." : activeCount}</p>
                </div>
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Paused</h2>
                    <p className="text-2xl font-bold text-yellow-400 mt-2">{loading ? "..." : pausedCount}</p>
                </div>
                <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
                    <h2 className="text-xl font-semibold text-white">Failed / Aborted</h2>
                    <p className="text-2xl font-bold text-red-400 mt-2">{loading ? "..." : failedCount}</p>
                </div>
            </div>
            
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Active Rollouts</h2>
                {error ? (
                    <div className="p-6 bg-red-900/20 border border-red-800 rounded-xl text-center space-y-3">
                        <p className="text-red-400 text-sm">{error}</p>
                        <button 
                            onClick={loadRollouts} 
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
                                <div className="h-6 bg-gray-700 rounded w-24"></div>
                            </div>
                        ))}
                    </div>
                ) : rollouts.length > 0 ? (
                    <div className="space-y-4">
                        {rollouts.map((rollout) => (
                            <Link key={rollout.id} href={`/app/rollouts/${rollout.id}`}>
                                <RolloutCard
                                    status={rollout.status || "draft"}
                                    name={rollout.name || `Rollout ${rollout.id.slice(0, 8)}`}
                                    stage={rollout.strategy_type || "Canary"}
                                />
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="p-8 bg-gray-850 border border-gray-800 rounded-xl text-center space-y-3">
                        <div className="w-12 h-12 mx-auto text-gray-500 flex items-center justify-center rounded-full bg-gray-800">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                        </div>
                        <h3 className="text-lg font-medium text-white">No active rollouts underway</h3>
                        <p className="text-gray-400 text-sm max-w-md mx-auto">No progressive rollout is currently in progress. Start a rollout to safely canary release changes.</p>
                        <Link href="/app/rollouts/new" className="inline-block mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition">
                            + Initialize New Rollout
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}

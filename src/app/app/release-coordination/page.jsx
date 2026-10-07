import React from 'react';
import Link from 'next/link';

export default function ReleaseCoordinationDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Release Coordination</h1>
                    <p className="text-gray-400 mt-2">Coordinate Portfolios, Release Trains, Dependencies, and Change Windows.</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/app/release-coordination/trains/new" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        Create Train
                    </Link>
                </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Link href="/app/release-coordination/trains" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">Release Trains</h2>
                    <p className="text-2xl font-bold text-blue-400 mt-2">4 Active</p>
                </Link>
                <Link href="/app/release-coordination/calendar" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-purple-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">Calendar</h2>
                    <p className="text-2xl font-bold text-purple-400 mt-2">View</p>
                </Link>
                <Link href="/app/release-coordination/conflicts" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-red-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">Conflicts</h2>
                    <p className="text-2xl font-bold text-red-400 mt-2">2 Blocking</p>
                </Link>
                <Link href="/app/release-coordination/windows" className="block p-6 bg-gray-800 rounded-xl border border-gray-700 hover:border-green-500 transition-colors text-center">
                    <h2 className="text-xl font-semibold text-white">Change Windows</h2>
                    <p className="text-2xl font-bold text-green-400 mt-2">1 Active</p>
                </Link>
            </div>
        </div>
    );
}
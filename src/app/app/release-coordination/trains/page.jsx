import React from 'react';
import Link from 'next/link';

export default function TrainsPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Release Trains</h1>
            <div className="space-y-4">
                <Link href="/app/release-coordination/trains/TRN-2026-10-A" className="block bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-gray-500">
                    <h3 className="font-semibold text-white text-lg">Q4 Major Intelligence Update</h3>
                    <p className="text-sm text-gray-400 mt-1">Status: Planning • 12 Releases • 2 Conflicts</p>
                </Link>
            </div>
        </div>
    );
}
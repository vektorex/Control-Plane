import React from 'react';
import Link from 'next/link';

export default function TrainDetail({ params }) {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h1 className="text-2xl font-bold text-white">Release Train <span className="font-mono text-gray-400 text-lg">#{params.trainId}</span></h1>
                <p className="text-gray-400 mt-1">Status: <span className="text-yellow-400">Blocked</span></p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href={`/app/release-coordination/trains/${params.trainId}/graph`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 text-center">
                    <h3 className="font-semibold">Dependency Graph</h3>
                </Link>
                <Link href={`/app/release-coordination/trains/${params.trainId}/waves`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-indigo-500 text-center">
                    <h3 className="font-semibold">Release Waves</h3>
                </Link>
                <Link href={`/app/release-coordination/trains/${params.trainId}/conflicts`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-red-500 text-center">
                    <h3 className="font-semibold text-red-400">Conflicts</h3>
                </Link>
                <Link href={`/app/release-coordination/trains/${params.trainId}/schedule`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-purple-500 text-center">
                    <h3 className="font-semibold">Schedule</h3>
                </Link>
                <Link href={`/app/release-coordination/trains/${params.trainId}/readiness`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-green-500 text-center">
                    <h3 className="font-semibold">Readiness</h3>
                </Link>
                <Link href={`/app/release-coordination/trains/${params.trainId}/impact`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-yellow-500 text-center">
                    <h3 className="font-semibold">Impact Analysis</h3>
                </Link>
                <Link href={`/app/release-coordination/trains/${params.trainId}/timeline`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-500 text-center">
                    <h3 className="font-semibold">Event Timeline</h3>
                </Link>
            </div>
        </div>
    );
}
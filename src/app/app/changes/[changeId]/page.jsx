import React from 'react';
import Link from 'next/link';

export default function ChangeDetail({ params }) {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Change Assessment</h1>
                    <p className="text-gray-400 font-mono text-sm mt-1">{params.changeId}</p>
                </div>
                <span className="px-4 py-2 bg-yellow-900/50 text-yellow-400 border border-yellow-800 rounded-lg font-medium">Impact Ready</span>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href={`/app/changes/${params.changeId}/impact`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 text-center">
                    <h3 className="font-semibold">Impact</h3>
                </Link>
                <Link href={`/app/changes/${params.changeId}/dependencies`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-indigo-500 text-center">
                    <h3 className="font-semibold">Dependencies</h3>
                </Link>
                <Link href={`/app/changes/${params.changeId}/risks`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-red-500 text-center">
                    <h3 className="font-semibold">Risks</h3>
                </Link>
                <Link href={`/app/changes/${params.changeId}/evidence`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-green-500 text-center">
                    <h3 className="font-semibold">Evidence</h3>
                </Link>
                <Link href={`/app/changes/${params.changeId}/simulation`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-purple-500 text-center">
                    <h3 className="font-semibold">Simulation</h3>
                </Link>
                <Link href={`/app/changes/${params.changeId}/rollback`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-orange-500 text-center">
                    <h3 className="font-semibold">Rollback</h3>
                </Link>
            </div>
        </div>
    );
}
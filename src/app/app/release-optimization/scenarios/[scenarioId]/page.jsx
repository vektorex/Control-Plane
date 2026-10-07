import React from 'react';
import Link from 'next/link';

export default function ScenarioDetail({ params }) {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Scenario <span className="font-mono text-gray-400 text-lg">#{params.scenarioId}</span></h1>
                    <p className="text-gray-400 mt-1">Status: <span className="text-green-400">Ready</span></p>
                </div>
                <div className="flex gap-2">
                    <Link href="/app/release-coordination" className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition">
                        Return to Release Coordination
                    </Link>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        Create Coordination Proposal
                    </button>
                </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/candidates`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 text-center">
                    <h3 className="font-semibold">Candidates</h3>
                </Link>
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/comparison`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-indigo-500 text-center">
                    <h3 className="font-semibold">Candidate Comparison</h3>
                </Link>
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/bottlenecks`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-red-500 text-center">
                    <h3 className="font-semibold text-red-400">Bottlenecks</h3>
                </Link>
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/sensitivity`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-purple-500 text-center">
                    <h3 className="font-semibold">Sensitivity Analysis</h3>
                </Link>
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/what-if`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-yellow-500 text-center">
                    <h3 className="font-semibold">What-If / Timeline</h3>
                </Link>
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/recommendations`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-green-500 text-center">
                    <h3 className="font-semibold">Recommendations</h3>
                </Link>
                <Link href={`/app/release-optimization/scenarios/${params.scenarioId}/evidence`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-500 text-center">
                    <h3 className="font-semibold">Provenance & Evidence</h3>
                </Link>
            </div>
        </div>
    );
}
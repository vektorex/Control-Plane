import React from 'react';
import Link from 'next/link';
import RolloutHeader from '@/components/rollouts/RolloutHeader';

export default function RolloutDetail({ params }) {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <RolloutHeader rolloutId={params.rolloutId} />
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href={`/app/rollouts/${params.rolloutId}/strategy`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 text-center">
                    <h3 className="font-semibold">Strategy & Plan</h3>
                </Link>
                <Link href={`/app/rollouts/${params.rolloutId}/stages`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-indigo-500 text-center">
                    <h3 className="font-semibold">Stages Timeline</h3>
                </Link>
                <Link href={`/app/rollouts/${params.rolloutId}/health`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-teal-500 text-center">
                    <h3 className="font-semibold">Health & Telemetry</h3>
                </Link>
                <Link href={`/app/rollouts/${params.rolloutId}/comparison`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-purple-500 text-center">
                    <h3 className="font-semibold">Baseline Comparison</h3>
                </Link>
                <Link href={`/app/rollouts/${params.rolloutId}/gates`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-green-500 text-center">
                    <h3 className="font-semibold">Evaluation Gates</h3>
                </Link>
                <Link href={`/app/rollouts/${params.rolloutId}/timeline`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-500 text-center">
                    <h3 className="font-semibold">Event Timeline</h3>
                </Link>
                <Link href={`/app/rollouts/${params.rolloutId}/rollback`} className="col-span-2 p-4 bg-red-900/20 border border-red-800 rounded-lg hover:border-red-500 text-center">
                    <h3 className="font-semibold text-red-400">Emergency Rollback</h3>
                </Link>
            </div>
        </div>
    );
}
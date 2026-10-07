import React from 'react';

export default function NewRollout() {
    return (
        <div className="p-6 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Configure Progressive Rollout</h1>
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <p className="text-gray-400">Select an approved release and choose a deployment strategy (e.g. Canary, Cohort, Percentage).</p>
            </div>
        </div>
    );
}
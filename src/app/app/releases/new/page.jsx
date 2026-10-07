import React from 'react';

export default function NewRelease() {
    return (
        <div className="p-6 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Create Release Candidate</h1>
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <p className="text-gray-400">Select an approved Change Request to bundle into a release.</p>
            </div>
        </div>
    );
}
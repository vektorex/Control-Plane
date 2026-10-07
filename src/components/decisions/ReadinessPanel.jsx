import React from 'react';
import BlockerList from './BlockerList';
import EvidencePanel from './EvidencePanel';

export default function ReadinessPanel({ decisionId }) {
    return (
        <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h2 className="text-lg font-semibold text-white mb-4">Overall Readiness</h2>
                <div className="p-4 bg-gray-900 rounded-lg border border-gray-800 flex items-center justify-between">
                    <span className="text-gray-300">State</span>
                    <span className="px-3 py-1 bg-yellow-900/50 text-yellow-400 border border-yellow-800 rounded text-sm font-medium">Conditionally Ready</span>
                </div>
            </div>
            <BlockerList limit={3} />
            <EvidencePanel limit={3} />
        </div>
    );
}
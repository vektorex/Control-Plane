import React from 'react';
import RolloutComparison from '@/components/rollouts/RolloutComparison';

export default function ComparisonPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Baseline vs Candidate</h1>
            <RolloutComparison />
        </div>
    );
}
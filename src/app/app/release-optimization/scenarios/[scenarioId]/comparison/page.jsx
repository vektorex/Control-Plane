import React from 'react';
import CandidateComparison from '@/components/release-optimization/CandidateComparison';

export default function ComparisonPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Compare Scenarios</h1>
            <CandidateComparison />
        </div>
    );
}
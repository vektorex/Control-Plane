import React from 'react';
import CandidateList from '@/components/release-optimization/CandidateList';

export default function CandidatesPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Optimization Candidates</h1>
            <CandidateList />
        </div>
    );
}
import React from 'react';
import RiskList from '@/components/changes/RiskList';

export default function RisksPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Risk Identification</h1>
            <RiskList />
        </div>
    );
}
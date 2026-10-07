import React from 'react';
import ImpactSummary from '@/components/changes/ImpactSummary';
import AffectedResourceList from '@/components/changes/AffectedResourceList';

export default function ImpactPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Impact Analysis</h1>
            <ImpactSummary />
            <AffectedResourceList />
        </div>
    );
}
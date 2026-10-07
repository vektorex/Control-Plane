import React from 'react';
import ReleaseImpact from '@/components/releases/ReleaseImpact';

export default function ImpactPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Change Impact & Diff</h1>
            <ReleaseImpact />
        </div>
    );
}
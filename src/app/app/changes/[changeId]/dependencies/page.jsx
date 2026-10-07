import React from 'react';
import DependencyImpact from '@/components/changes/DependencyImpact';
import ChangeGraph from '@/components/changes/ChangeGraph';

export default function DependenciesPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Dependency Impact</h1>
            <DependencyImpact />
            <ChangeGraph />
        </div>
    );
}
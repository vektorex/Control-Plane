import React from 'react';
import DependencyGraph from '@/components/release-coordination/DependencyGraph';

export default function GraphPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Dependency DAG</h1>
            <DependencyGraph />
        </div>
    );
}
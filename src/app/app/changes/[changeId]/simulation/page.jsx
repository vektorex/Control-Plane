import React from 'react';
import SimulationPanel from '@/components/changes/SimulationPanel';

export default function SimulationPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Change Simulation (Non-Production)</h1>
            <SimulationPanel />
        </div>
    );
}
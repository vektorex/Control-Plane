import React from 'react';
import RolloutHealth from '@/components/rollouts/RolloutHealth';

export default function HealthPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Rollout Health Observation</h1>
            <p className="text-gray-400">Continuous telemetry matching existing domain capabilities. No fabricated scores.</p>
            <RolloutHealth />
        </div>
    );
}
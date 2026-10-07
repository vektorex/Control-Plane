import React from 'react';
import RolloutStrategy from '@/components/rollouts/RolloutStrategy';

export default function StrategyPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Rollout Strategy</h1>
            <RolloutStrategy />
        </div>
    );
}
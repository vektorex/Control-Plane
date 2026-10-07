import React from 'react';
import RolloutStageTimeline from '@/components/rollouts/RolloutStageTimeline';
import RolloutProgress from '@/components/rollouts/RolloutProgress';

export default function StagesPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Progressive Stages</h1>
            <RolloutProgress />
            <RolloutStageTimeline />
        </div>
    );
}
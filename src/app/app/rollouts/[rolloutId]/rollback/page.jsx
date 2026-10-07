import React from 'react';
import RolloutRollback from '@/components/rollouts/RolloutRollback';

export default function RollbackPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-red-400">Rollout Abort & Rollback</h1>
            <RolloutRollback />
        </div>
    );
}
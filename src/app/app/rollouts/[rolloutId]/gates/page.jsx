import React from 'react';
import RolloutGate from '@/components/rollouts/RolloutGate';

export default function GatesPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Evaluation & Verification Gates</h1>
            <div className="space-y-4">
                <RolloutGate type="Evaluation Suite" status="passed" details="Smoke tests passed. 0 regressions." />
                <RolloutGate type="Error Rate" status="unknown" details="Telemetry missing. Stage paused." />
                <RolloutGate type="Security Scanners" status="passed" details="No new incidents." />
            </div>
        </div>
    );
}
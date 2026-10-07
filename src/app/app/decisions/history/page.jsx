import React from 'react';
import DecisionTimeline from '@/components/decisions/DecisionTimeline';

export default function DecisionHistoryPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Decision History</h1>
            <DecisionTimeline />
        </div>
    );
}
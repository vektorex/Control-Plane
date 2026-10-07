import React from 'react';
import ChangeTimeline from '@/components/changes/ChangeTimeline';

export default function HistoryPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Change History</h1>
            <ChangeTimeline />
        </div>
    );
}
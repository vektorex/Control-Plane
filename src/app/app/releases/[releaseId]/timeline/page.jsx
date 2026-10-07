import React from 'react';
import ReleaseTimeline from '@/components/releases/ReleaseTimeline';

export default function TimelinePage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Immutable Audit Timeline</h1>
            <ReleaseTimeline />
        </div>
    );
}
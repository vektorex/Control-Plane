import React from 'react';
import TrainSchedule from '@/components/release-coordination/TrainSchedule';

export default function SchedulePage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Train Schedule</h1>
            <TrainSchedule />
        </div>
    );
}
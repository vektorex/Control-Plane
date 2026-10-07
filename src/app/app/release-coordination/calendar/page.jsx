import React from 'react';
import ReleaseCalendar from '@/components/release-coordination/ReleaseCalendar';

export default function CalendarPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Release Calendar</h1>
            <ReleaseCalendar />
        </div>
    );
}
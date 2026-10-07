import React from 'react';
import ReleasePlan from '@/components/releases/ReleasePlan';

export default function PlanPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Release Plan</h1>
            <ReleasePlan />
        </div>
    );
}
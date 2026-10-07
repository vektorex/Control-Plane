import React from 'react';
import ReadinessState from '@/components/decisions/ReadinessState';

export default function ReadinessDashboard() {
    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Execution Readiness Assessments</h1>
            <ReadinessState />
        </div>
    );
}
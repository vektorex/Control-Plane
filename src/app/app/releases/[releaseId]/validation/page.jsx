import React from 'react';
import ReleaseValidation from '@/components/releases/ReleaseValidation';

export default function ValidationPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Stage Validation</h1>
            <ReleaseValidation />
        </div>
    );
}
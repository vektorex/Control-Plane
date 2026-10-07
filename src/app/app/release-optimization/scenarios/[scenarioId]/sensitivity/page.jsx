import React from 'react';
import SensitivityView from '@/components/release-optimization/SensitivityView';

export default function SensitivityPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Sensitivity Analysis</h1>
            <SensitivityView />
        </div>
    );
}
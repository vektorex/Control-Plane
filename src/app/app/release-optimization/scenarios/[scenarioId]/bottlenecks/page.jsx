import React from 'react';
import BottleneckView from '@/components/release-optimization/BottleneckView';

export default function BottlenecksPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-red-400">Bottleneck Analysis</h1>
            <BottleneckView />
        </div>
    );
}
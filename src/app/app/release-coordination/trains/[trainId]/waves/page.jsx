import React from 'react';
import WaveManager from '@/components/release-coordination/WaveManager';

export default function WavesPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Release Waves</h1>
            <WaveManager />
        </div>
    );
}
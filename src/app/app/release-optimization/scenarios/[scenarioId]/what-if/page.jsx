import React from 'react';
import WhatIfTimeline from '@/components/release-optimization/WhatIfTimeline';

export default function WhatIfPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">What-If / Timeline Analysis</h1>
            <WhatIfTimeline />
        </div>
    );
}
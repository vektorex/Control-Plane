import React from 'react';
import EvidencePanel from '@/components/decisions/EvidencePanel';

export default function EvidencePage() {
    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Evidence Collection</h1>
            <EvidencePanel />
        </div>
    );
}
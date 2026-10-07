import React from 'react';
import EvidencePanel from '@/components/changes/EvidencePanel';

export default function EvidencePage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Provenance & Evidence</h1>
            <EvidencePanel />
        </div>
    );
}
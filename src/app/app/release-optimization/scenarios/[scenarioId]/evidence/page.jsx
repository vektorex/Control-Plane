import React from 'react';
import ProvenanceLog from '@/components/release-optimization/ProvenanceLog';

export default function EvidencePage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Evidence & Provenance</h1>
            <ProvenanceLog />
        </div>
    );
}
import React from 'react';
import VerificationPanel from '@/components/releases/VerificationPanel';

export default function VerificationPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Post-Deployment Verification & Observation</h1>
            <VerificationPanel />
        </div>
    );
}
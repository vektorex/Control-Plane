import React from 'react';
import ReleaseApproval from '@/components/releases/ReleaseApproval';

export default function ApprovalsPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Release Approvals</h1>
            <ReleaseApproval />
        </div>
    );
}
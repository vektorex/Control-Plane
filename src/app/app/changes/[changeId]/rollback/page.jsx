import React from 'react';
import RollbackPanel from '@/components/changes/RollbackPanel';

export default function RollbackPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Rollback Analysis</h1>
            <RollbackPanel />
        </div>
    );
}
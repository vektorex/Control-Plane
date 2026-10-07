import React from 'react';
import RollbackPanel from '@/components/releases/RollbackPanel';

export default function RollbackPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-orange-400">Release Rollback</h1>
            <RollbackPanel />
        </div>
    );
}
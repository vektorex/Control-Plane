import React from 'react';
import ConflictCenter from '@/components/release-coordination/ConflictCenter';

export default function ConflictsPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-red-400">Conflict Center</h1>
            <ConflictCenter />
        </div>
    );
}
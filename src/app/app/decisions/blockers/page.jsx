import React from 'react';
import BlockerList from '@/components/decisions/BlockerList';
import DecisionFilters from '@/components/decisions/DecisionFilters';

export default function BlockersPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Active Blockers</h1>
            <DecisionFilters type="blockers" />
            <div className="mt-6">
                <BlockerList />
            </div>
        </div>
    );
}
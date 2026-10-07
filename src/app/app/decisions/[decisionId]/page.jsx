import React from 'react';
import DecisionHeader from '@/components/decisions/DecisionHeader';
import ReadinessPanel from '@/components/decisions/ReadinessPanel';

export default function DecisionDetail({ params }) {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <DecisionHeader decisionId={params.decisionId} />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <ReadinessPanel decisionId={params.decisionId} />
                </div>
                <div>
                    {/* Additional details */}
                </div>
            </div>
        </div>
    );
}
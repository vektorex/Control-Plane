import React from 'react';
import RecommendationEngine from '@/components/release-optimization/RecommendationEngine';

export default function RecommendationsPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Optimization Recommendations</h1>
            <RecommendationEngine />
        </div>
    );
}
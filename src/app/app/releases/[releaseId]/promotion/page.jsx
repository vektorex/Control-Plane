import React from 'react';
import PromotionControls from '@/components/releases/PromotionControls';

export default function PromotionPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-purple-400">Production Promotion</h1>
            <p className="text-gray-400">Explicitly authorized mutation of authoritative domain resources.</p>
            <PromotionControls />
        </div>
    );
}
import React from 'react';
import FreezeBanner from '@/components/releases/FreezeBanner';

export default function SettingsPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Release Settings</h1>
            <FreezeBanner />
        </div>
    );
}
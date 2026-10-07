import React from 'react';
import EnvironmentBadge from '@/components/releases/EnvironmentBadge';

export default function EnvironmentsPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">Logical Environments</h1>
            <div className="space-y-4">
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold">Development</h2>
                        <p className="text-gray-400">Sandbox configuration</p>
                    </div>
                    <EnvironmentBadge type="development" />
                </div>
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold">Staging</h2>
                        <p className="text-gray-400">Pre-production evaluation and testing</p>
                    </div>
                    <EnvironmentBadge type="staging" />
                </div>
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold">Production</h2>
                        <p className="text-gray-400">Authoritative live services</p>
                    </div>
                    <EnvironmentBadge type="production" />
                </div>
            </div>
        </div>
    );
}
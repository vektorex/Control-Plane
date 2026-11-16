import React from 'react';
import Link from 'next/link';
import ReleaseHeader from '@/components/releases/ReleaseHeader';

export default async function ReleaseDetail({ params }) {
    const { releaseId } = await params;
    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <ReleaseHeader releaseId={releaseId} />
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href={`/app/releases/${releaseId}/plan`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 text-center">
                    <h3 className="font-semibold">Plan & Stages</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/impact`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-indigo-500 text-center">
                    <h3 className="font-semibold">Impact Analysis</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/approvals`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-teal-500 text-center">
                    <h3 className="font-semibold">Approvals</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/validation`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-green-500 text-center">
                    <h3 className="font-semibold">Validation</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/promotion`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-purple-500 text-center">
                    <h3 className="font-semibold text-purple-400">Promotion</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/verification`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 text-center">
                    <h3 className="font-semibold">Verification</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/rollback`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-orange-500 text-center">
                    <h3 className="font-semibold">Rollback</h3>
                </Link>
                <Link href={`/app/releases/${releaseId}/timeline`} className="p-4 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-500 text-center">
                    <h3 className="font-semibold">Timeline</h3>
                </Link>
            </div>
        </div>
    );
}
import React from 'react';
import ChangeBuilder from '@/components/changes/ChangeBuilder';

export default function NewChangeRequest() {
    return (
        <div className="p-6 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold mb-6">Propose New Change</h1>
            <ChangeBuilder />
        </div>
    );
}
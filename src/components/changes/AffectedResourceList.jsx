export default function AffectedResourceList() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Affected Resources</h2>
            <div className="space-y-3">
                <div className="p-4 bg-gray-900 rounded-lg border border-gray-800">
                    <p className="font-medium text-white">Solution: Security Scanner</p>
                    <p className="text-sm text-gray-400 mt-1">Impact: Transitive dependency version change.</p>
                </div>
            </div>
        </div>
    );
}
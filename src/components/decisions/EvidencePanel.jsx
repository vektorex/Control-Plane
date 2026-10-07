export default function EvidencePanel({ limit }) {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Collected Evidence</h2>
            <div className="space-y-3">
                <div className="p-4 bg-gray-900 border border-gray-800 rounded-lg">
                    <div className="flex justify-between">
                        <p className="font-medium text-white">Security Scan Passed</p>
                        <span className="text-green-400 text-sm">Verified</span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">Source: Security Tooling V2</p>
                </div>
            </div>
        </div>
    );
}
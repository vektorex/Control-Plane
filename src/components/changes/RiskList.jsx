export default function RiskList() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Identified Risks</h2>
            <div className="space-y-3">
                <div className="p-4 bg-red-900/10 border border-red-900/50 rounded-lg">
                    <p className="font-medium text-red-400">Governance Policy Violation</p>
                    <p className="text-sm text-gray-400 mt-1">Target model is not approved for restricted data.</p>
                </div>
            </div>
        </div>
    );
}
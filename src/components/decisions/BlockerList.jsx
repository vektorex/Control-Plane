export default function BlockerList({ limit }) {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
                <span className="bg-red-500/20 text-red-400 p-1 rounded mr-2 border border-red-500/50 text-xs">2</span>
                Active Blockers
            </h2>
            <div className="space-y-3">
                <div className="p-4 bg-red-900/10 border border-red-900/50 rounded-lg">
                    <p className="font-medium text-red-400">Missing Governance Approval</p>
                    <p className="text-sm text-gray-400 mt-1">Mandatory policy 'Data Processing' requires approval.</p>
                </div>
                <div className="p-4 bg-orange-900/10 border border-orange-900/50 rounded-lg">
                    <p className="font-medium text-orange-400">Unhealthy Dependency</p>
                    <p className="text-sm text-gray-400 mt-1">Connector 'Salesforce CRM' is currently down.</p>
                </div>
            </div>
        </div>
    );
}
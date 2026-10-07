export default function WaveManager() {
    return (
        <div className="space-y-4">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="font-bold text-white mb-2">Wave 1: Data Connectors</h3>
                <p className="text-gray-400 text-sm">3 Releases. Status: Ready.</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 opacity-50">
                <h3 className="font-bold text-gray-400 mb-2">Wave 2: Analytics Agents</h3>
                <p className="text-gray-500 text-sm">Requires Wave 1.</p>
            </div>
        </div>
    );
}
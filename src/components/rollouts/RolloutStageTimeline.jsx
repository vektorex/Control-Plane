export default function RolloutStageTimeline() {
    return (
        <div className="space-y-4">
            <div className="p-4 bg-gray-800 border-l-4 border-green-500 rounded">
                <div className="font-bold text-green-400">Stage 1: 5% (Completed)</div>
                <div className="text-sm text-gray-400">All gates passed. Observed for 15m.</div>
            </div>
            <div className="p-4 bg-blue-900/20 border-l-4 border-blue-500 rounded">
                <div className="font-bold text-blue-400">Stage 2: 25% (Observing)</div>
                <div className="text-sm text-gray-400">Evaluating health signals. 8m remaining.</div>
            </div>
            <div className="p-4 bg-gray-800 border-l-4 border-gray-600 rounded opacity-50">
                <div className="font-bold text-gray-400">Stage 3: 50% (Pending)</div>
            </div>
            <div className="p-4 bg-gray-800 border-l-4 border-gray-600 rounded opacity-50">
                <div className="font-bold text-gray-400">Stage 4: 100% (Pending)</div>
            </div>
        </div>
    );
}
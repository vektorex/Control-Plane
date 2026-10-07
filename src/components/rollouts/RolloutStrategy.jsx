export default function RolloutStrategy() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="text-lg font-bold text-white mb-2">Strategy Configuration</h3>
            <pre className="p-4 bg-gray-900 rounded border border-gray-700 text-sm text-gray-300">
{JSON.stringify({
    type: "percentage",
    stages: [5, 25, 50, 100],
    observationWindow: "15m",
    autoAdvance: true
}, null, 2)}
            </pre>
        </div>
    );
}
export default function RolloutHeader({ rolloutId }) {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex justify-between items-center">
            <div>
                <h1 className="text-2xl font-bold text-white">Rollout <span className="font-mono text-gray-400 text-lg">#{rolloutId.slice(0, 8)}</span></h1>
                <p className="text-gray-400 mt-1">Strategy: <span className="text-purple-400">Percentage Canary</span></p>
            </div>
            <div className="flex gap-2">
                <button className="px-4 py-2 bg-yellow-600/20 text-yellow-400 border border-yellow-800 rounded hover:bg-yellow-600/30 font-medium">Pause</button>
                <button className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-800 rounded hover:bg-red-600/30 font-medium">Abort</button>
            </div>
        </div>
    );
}
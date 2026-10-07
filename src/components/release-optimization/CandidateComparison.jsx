export default function CandidateComparison() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="grid grid-cols-3 gap-4 border-b border-gray-700 pb-4 mb-4">
                <div className="font-bold text-gray-400">Metric</div>
                <div className="font-bold text-white">Baseline</div>
                <div className="font-bold text-white">Candidate 2</div>
            </div>
            <div className="grid grid-cols-3 gap-4 py-2 border-b border-gray-700/50">
                <div className="text-gray-400">Waves</div>
                <div className="text-white">4</div>
                <div className="text-green-400">3</div>
            </div>
            <div className="grid grid-cols-3 gap-4 py-2 border-b border-gray-700/50">
                <div className="text-gray-400">Blocking Conflicts</div>
                <div className="text-white">0</div>
                <div className="text-white">0</div>
            </div>
            <div className="grid grid-cols-3 gap-4 py-2">
                <div className="text-gray-400">Contract Impact</div>
                <div className="text-white">None</div>
                <div className="text-yellow-400">Tight Window (2h buffer)</div>
            </div>
        </div>
    );
}
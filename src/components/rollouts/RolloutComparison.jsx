export default function RolloutComparison() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 grid grid-cols-2 gap-6">
            <div>
                <h3 className="font-bold text-gray-300 mb-4">Baseline (v1.2)</h3>
                <div className="space-y-2">
                    <div className="flex justify-between border-b border-gray-700 pb-1"><span>Latency</span><span>120ms</span></div>
                    <div className="flex justify-between border-b border-gray-700 pb-1"><span>Errors</span><span>0.01%</span></div>
                </div>
            </div>
            <div>
                <h3 className="font-bold text-blue-400 mb-4">Candidate (v1.3)</h3>
                <div className="space-y-2">
                    <div className="flex justify-between border-b border-gray-700 pb-1"><span>Latency</span><span className="text-green-400">95ms</span></div>
                    <div className="flex justify-between border-b border-gray-700 pb-1"><span>Errors</span><span>0.01%</span></div>
                </div>
            </div>
        </div>
    );
}
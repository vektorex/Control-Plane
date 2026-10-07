export default function CandidateList() {
    return (
        <div className="space-y-4">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="font-bold text-white mb-2">Candidate 1 (Baseline)</h3>
                <p className="text-gray-400 text-sm">Follows explicit order from STEP 55 without changes.</p>
            </div>
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                <h3 className="font-bold text-white mb-2">Candidate 2 (Aggressive Waves)</h3>
                <p className="text-gray-400 text-sm">Packs wave 1 to capacity limit. 12% faster schedule.</p>
            </div>
        </div>
    );
}
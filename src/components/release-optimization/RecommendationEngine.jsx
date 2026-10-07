export default function RecommendationEngine() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 className="font-bold text-white mb-2">Move Release B after Release A</h3>
            <p className="text-gray-400 text-sm mb-4">Release B implicitly requires the output of Release A based on data structure analysis.</p>
            <div className="mt-4 p-4 bg-purple-900/20 border border-purple-800 rounded">
                <p className="text-purple-400 text-xs font-bold uppercase mb-1">AI_SUGGESTION</p>
                <p className="text-gray-300 text-sm">Separating Release C and D avoids targeting the same constrained environment simultaneously.</p>
            </div>
        </div>
    );
}
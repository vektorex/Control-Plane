export default function DecisionHeader({ decisionId }) {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex justify-between items-center">
            <div>
                <h1 className="text-2xl font-bold text-white">Decision Assessment</h1>
                <p className="text-gray-400 font-mono text-sm mt-1">{decisionId}</p>
            </div>
            <div className="px-4 py-2 bg-blue-900/50 text-blue-400 border border-blue-800 rounded-lg font-medium">
                Evaluating...
            </div>
        </div>
    );
}
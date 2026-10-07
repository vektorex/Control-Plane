export default function ConflictCenter() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-red-500/30">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="font-bold text-white text-lg">Dependency Cycle Detected</h3>
                    <p className="text-red-400 mt-1">Severity: BLOCKING</p>
                </div>
            </div>
            <p className="text-gray-400 text-sm">REL-A requires REL-B, but REL-B requires REL-A.</p>
            <div className="mt-4 p-4 bg-purple-900/20 border border-purple-800 rounded">
                <p className="text-purple-400 text-xs font-bold uppercase mb-1">AI_SUGGESTION</p>
                <p className="text-gray-300 text-sm">Remove the explicit dependency from REL-B to REL-A, as it appears to be a misconfiguration.</p>
            </div>
        </div>
    );
}
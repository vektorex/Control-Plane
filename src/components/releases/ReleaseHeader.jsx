export default function ReleaseHeader({ releaseId }) {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex justify-between items-center">
            <div>
                <h1 className="text-2xl font-bold text-white">Release <span className="font-mono text-gray-400 text-lg">#{releaseId.slice(0, 8)}</span></h1>
                <p className="text-gray-400 mt-1">Status: <span className="text-blue-400">Planning</span></p>
            </div>
            <div className="flex gap-2">
                <span className="px-3 py-1 bg-yellow-900/50 text-yellow-400 border border-yellow-800 rounded">Staging</span>
                <span className="px-3 py-1 bg-purple-900/50 text-purple-400 border border-purple-800 rounded">Production</span>
            </div>
        </div>
    );
}
export default function RolloutRollback() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-red-500/30 text-center space-y-4">
            <h2 className="text-xl font-bold text-white">Abort & Rollback</h2>
            <p className="text-gray-400 max-w-md mx-auto">This will immediately pause the rollout, prevent future stages, and request a full rollback from STEP 53 Releases.</p>
            <button className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-lg shadow-red-900/50 transition">
                CONFIRM ROLLBACK
            </button>
        </div>
    );
}
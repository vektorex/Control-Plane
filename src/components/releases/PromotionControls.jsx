export default function PromotionControls() {
    return (
        <div className="bg-gray-800 p-8 rounded-xl border border-purple-500/30 text-center space-y-4">
            <h2 className="text-xl font-bold text-white">Ready for Production</h2>
            <p className="text-gray-400 max-w-md mx-auto">All preconditions, impacts, decisions, freezes, locks, and approvals have been verified.</p>
            <button className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-lg shadow-purple-900/50 transition">
                PROMOTE TO PRODUCTION
            </button>
        </div>
    );
}
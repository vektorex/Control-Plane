export default function RollbackPanel() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Rollback Feasibility</h2>
            <div className="p-4 bg-green-900/10 border border-green-900/50 rounded-lg">
                <p className="font-medium text-green-400">Rollback Possible</p>
                <p className="text-sm text-gray-400 mt-1">Previous immutable version can be restored without data loss.</p>
            </div>
        </div>
    );
}
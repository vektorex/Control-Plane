export default function RollbackPanel() {
    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <p className="text-gray-400 mb-4">If verification fails or telemetry degrades, initiate rollback to source_version.</p>
            <button className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-800 rounded hover:bg-red-600/30 transition">
                Request Rollback
            </button>
        </div>
    );
}